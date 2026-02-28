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
        """Analyze fitness competition in area."""
        competitors = self.search_nearby(lat, lng, radius, PLACE_TYPES['competitors'])
        
        total_competitors = len(competitors)
        avg_rating = sum(c.get('rating', 0) for c in competitors) / total_competitors if total_competitors > 0 else 0
        highly_rated = sum(1 for c in competitors if c.get('rating', 0) >= 4.0)
        
        return {
            'count': total_competitors,
            'competitors': competitors,
            'average_rating': round(avg_rating, 1),
            'highly_rated_count': highly_rated,
            'density_score': max(0, 100 - (total_competitors * 15)),
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