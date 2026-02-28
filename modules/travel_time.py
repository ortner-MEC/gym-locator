"""Enhanced travel time and isochrone analysis."""
import urllib.request
import urllib.parse
import json
import math
from typing import List, Dict, Tuple
from config import GOOGLE_DISTANCE_API_KEY

class TravelTimeAnalyzer:
    """Analyzes reachability using travel time isochrones."""
    
    def __init__(self, api_key: str = GOOGLE_DISTANCE_API_KEY):
        self.api_key = api_key
        self.base_url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    
    def _generate_grid_points(self, center_lat: float, center_lng: float, 
                             radius_km: float = 2.0, grid_size: int = 10) -> List[Tuple[float, float]]:
        """Generate a grid of points around center for isochrone analysis."""
        points = []
        
        # Convert km to degrees (approximate)
        lat_step = radius_km / 111.0  # 1 degree lat ≈ 111km
        lng_step = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        for i in range(-grid_size, grid_size + 1):
            for j in range(-grid_size, grid_size + 1):
                lat = center_lat + (i * lat_step / grid_size)
                lng = center_lng + (j * lng_step / grid_size)
                points.append((lat, lng))
        
        return points
    
    def calculate_travel_times(self, origin_lat: float, origin_lng: float,
                              destinations: List[Tuple[float, float]],
                              mode: str = 'walking') -> List[Dict]:
        """Calculate travel times to multiple destinations (batch)."""
        if not destinations:
            return []
        
        # Google Distance Matrix max 25 destinations per request
        results = []
        batch_size = 25
        
        for i in range(0, len(destinations), batch_size):
            batch = destinations[i:i + batch_size]
            batch_results = self._make_distance_request(
                origin_lat, origin_lng, batch, mode
            )
            results.extend(batch_results)
        
        return results
    
    def _make_distance_request(self, origin_lat: float, origin_lng: float,
                              destinations: List[Tuple[float, float]],
                              mode: str) -> List[Dict]:
        """Single Distance Matrix API request."""
        dest_strings = [f"{lat},{lng}" for lat, lng in destinations]
        origins = f"{origin_lat},{origin_lng}"
        
        params = {
            'origins': origins,
            'destinations': '|'.join(dest_strings),
            'mode': mode,
            'key': self.api_key
        }
        
        try:
            query_string = urllib.parse.urlencode(params)
            url = f"{self.base_url}?{query_string}"
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data['status'] != 'OK':
                return [{'duration_min': None, 'distance_km': None, 'error': data['status']} 
                       for _ in destinations]
            
            elements = data['rows'][0]['elements']
            results = []
            
            for elem in elements:
                if elem['status'] == 'OK':
                    results.append({
                        'duration_min': elem['duration']['value'] / 60,
                        'distance_km': elem['distance']['value'] / 1000,
                        'status': 'OK'
                    })
                else:
                    results.append({
                        'duration_min': None,
                        'distance_km': None,
                        'status': elem['status']
                    })
            
            return results
            
        except Exception as e:
            print(f"Distance API error: {e}")
            return [{'duration_min': None, 'distance_km': None, 'error': str(e)} 
                   for _ in destinations]
    
    def analyze_isochrones(self, lat: float, lng: float) -> Dict:
        """Analyze how many grid points are reachable in different time bands."""
        print("\n⏱️  Berechne Fahrzeit-Isochronen...")
        
        # Generate grid points in 2km radius
        grid_points = self._generate_grid_points(lat, lng, radius_km=2.0, grid_size=8)
        print(f"   Grid: {len(grid_points)} Testpunkte generiert")
        
        # Walking times
        walking_results = self.calculate_travel_times(lat, lng, grid_points, 'walking')
        
        # Driving times (sample every 4th point to save API calls)
        driving_points = grid_points[::4]
        driving_results = self.calculate_travel_times(lat, lng, driving_points, 'driving')
        
        # Analyze walking reachability
        walking_5min = sum(1 for r in walking_results if r['duration_min'] and r['duration_min'] <= 5)
        walking_10min = sum(1 for r in walking_results if r['duration_min'] and r['duration_min'] <= 10)
        walking_15min = sum(1 for r in walking_results if r['duration_min'] and r['duration_min'] <= 15)
        
        # Analyze driving reachability
        driving_5min = sum(1 for r in driving_results if r['duration_min'] and r['duration_min'] <= 5)
        driving_10min = sum(1 for r in driving_results if r['duration_min'] and r['duration_min'] <= 10)
        driving_15min = sum(1 for r in driving_results if r['duration_min'] and r['duration_min'] <= 15)
        
        # Estimate population reach (rough: each grid point ≈ area with population)
        # 2km radius ≈ 12.5km², grid_size 8x8 = 16x16 grid = 256 points
        # Each point ≈ 50,000m² / 256 ≈ 195 people (Madrid avg ~2000/km²)
        people_per_point = 195  # Rough estimate
        
        walking_reach_10min = walking_10min * people_per_point
        driving_reach_10min = driving_10min * people_per_point * 4  # Driving covers more area
        
        avg_walking_time = sum(r['duration_min'] for r in walking_results if r['duration_min']) / len([r for r in walking_results if r['duration_min']]) if walking_results else 0
        
        return {
            'walking': {
                '5min_reach': walking_5min,
                '10min_reach': walking_10min,
                '15min_reach': walking_15min,
                'estimated_population_10min': int(walking_reach_10min),
                'coverage_percentage': round(walking_10min / len(grid_points) * 100, 1),
                'average_time': round(avg_walking_time, 1)
            },
            'driving': {
                '5min_reach': driving_5min,
                '10min_reach': driving_10min,
                '15min_reach': driving_15min,
                'estimated_population_10min': int(driving_reach_10min),
            },
            'score': self._calculate_reachability_score(walking_10min, len(grid_points))
        }
    
    def _calculate_reachability_score(self, reachable_points: int, total_points: int) -> int:
        """Calculate reachability score 0-100."""
        if total_points == 0:
            return 0
        
        coverage = reachable_points / total_points
        # 50%+ coverage = excellent (100 pts), 10% = poor (0 pts)
        score = min(100, max(0, (coverage - 0.1) * 250))
        return int(score)
    
    def get_competitor_travel_comparison(self, origin_lat: float, origin_lng: float,
                                        competitor_locations: List[Dict]) -> Dict:
        """Compare travel times to competitor locations."""
        if not competitor_locations:
            return {'comparison': 'No competitors found'}
        
        # Sample 3 competitors
        sample_competitors = competitor_locations[:3]
        competitor_coords = [
            (c['location']['latitude'], c['location']['longitude'])
            for c in sample_competitors if 'location' in c
        ]
        
        if not competitor_coords:
            return {'comparison': 'No valid competitor coordinates'}
        
        # To you
        your_times = self.calculate_travel_times(origin_lat, origin_lng, 
                                                  competitor_coords, 'walking')
        avg_to_you = sum(r['duration_min'] for r in your_times if r['duration_min']) / len([r for r in your_times if r['duration_min']]) if your_times else 0
        
        return {
            'your_location_accessibility': 'Good' if avg_to_you < 15 else 'Limited',
            'avg_time_from_competitors': round(avg_to_you, 1),
            'competitor_count_analyzed': len(sample_competitors)
        }