"""Google Places API wrapper for gym location analysis."""
import urllib.request
import urllib.error
import urllib.parse
import json
from typing import List, Dict, Optional
from config import GOOGLE_PLACES_API_KEY, PLACE_TYPES

BASE_URL = 'https://places.googleapis.com/v1/places'

class PlacesAPI:
    def __init__(self, api_key: str = GOOGLE_PLACES_API_KEY):
        self.api_key = api_key

    def _make_request(self, url: str, data: dict = None, headers: dict = None) -> dict:
        """Make HTTP request and return JSON response."""
        req = urllib.request.Request(url, method='POST' if data else 'GET')
        
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        if data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP Error {e.code}: {error_body}")
            return {}
        except Exception as e:
            print(f"Request error: {e}")
            return {}

    def search_nearby(self, lat: float, lng: float, radius: int, place_types: List[str]) -> List[Dict]:
        """Search for places near a location."""
        url = f'{BASE_URL}:searchNearby'
        
        headers = {
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.businessStatus'
        }
        
        body = {
            'locationRestriction': {
                'circle': {
                    'center': {'latitude': lat, 'longitude': lng},
                    'radius': radius
                }
            },
            'includedTypes': place_types,
            'maxResultCount': 20
        }
        
        data = self._make_request(url, body, headers)
        return data.get('places', [])

    def geocode_address(self, address: str) -> Optional[tuple]:
        """Convert address to coordinates using Geocoding API."""
        encoded_address = urllib.parse.quote(address)
        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={self.api_key}'
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data['status'] == 'OK':
                    location = data['results'][0]['geometry']['location']
                    return (location['lat'], location['lng'])
                else:
                    print(f"Geocoding error: {data['status']}")
                    return None
        except Exception as e:
            print(f"Error geocoding: {e}")
            return None

    def analyze_competition(self, lat: float, lng: float, radius: int) -> Dict:
        """Analyze fitness competition in area with intelligent filtering and distance weighting."""
        from modules.competition_intelligence import CompetitionIntelligence
        
        competitors = self.search_nearby(lat, lng, radius, PLACE_TYPES['competitors'])
        
        # Use AI-based filtering with distance calculation
        intelligence = CompetitionIntelligence(origin_lat=lat, origin_lng=lng)
        filtered = intelligence.filter_real_competition(competitors)
        
        return {
            'count': filtered['real_count'],
            'total_found': filtered['total_found'],
            'competitors': filtered['real_competitors'],
            'filtered_out': filtered['not_competition'],
            'unclear': filtered['unclear'],
            'average_rating': filtered['average_rating'],
            'highly_rated_count': filtered['highly_rated_count'],
            'avg_distance_m': filtered.get('avg_distance_m'),
            'closest_competitor': filtered.get('closest_competitor'),
            'density_score': filtered['density_score'],
            'market_saturation': filtered['market_saturation'],
            'filtering_explanation': intelligence.generate_explanation(filtered)
        }

    def analyze_target_demographics(self, lat: float, lng: float, radius: int) -> Dict:
        """Analyze target demographic presence."""
        residential = self.search_nearby(lat, lng, radius, PLACE_TYPES['target_residential'])
        offices = self.search_nearby(lat, lng, radius, PLACE_TYPES['target_office'])
        young = self.search_nearby(lat, lng, radius, PLACE_TYPES['target_young'])
        
        total_score = min(100, (len(residential) * 5) + (len(offices) * 3) + (len(young) * 8))
        
        return {
            'residential_count': len(residential),
            'office_count': len(offices),
            'young_count': len(young),
            'demographic_score': total_score,
            'primary_target': 'young_professionals' if len(young) > 2 else 'residents'
        }

    def analyze_accessibility(self, lat: float, lng: float, radius: int) -> Dict:
        """Analyze accessibility (transport, parking)."""
        transport = self.search_nearby(lat, lng, radius, ['subway_station', 'bus_station', 'train_station'])
        parking = self.search_nearby(lat, lng, radius, ['parking'])
        
        score = min(100, (len(transport) * 20) + (len(parking) * 5))
        
        return {
            'public_transport_count': len(transport),
            'parking_count': len(parking),
            'accessibility_score': score,
            'transport_types': [t.get('displayName', {}).get('text', '') for t in transport[:3]]
        }