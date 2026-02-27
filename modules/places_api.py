"""Google Places API wrapper for gym location analysis."""
import requests
import json
from typing import List, Dict, Optional
from config import GOOGLE_PLACES_API_KEY, PLACE_TYPES

BASE_URL = 'https://places.googleapis.com/v1/places'

class PlacesAPI:
    def __init__(self, api_key: str = GOOGLE_PLACES_API_KEY):
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.businessStatus'
        }

    def search_nearby(self, lat: float, lng: float, radius: int, place_types: List[str]) -> List[Dict]:
        """Search for places near a location."""
        url = f'{BASE_URL}:searchNearby'
        
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
        
        try:
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data.get('places', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching places: {e}")
            return []

    def geocode_address(self, address: str) -> Optional[tuple]:
        """Convert address to coordinates using Geocoding API."""
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': address,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
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
            'density_score': max(0, 100 - (total_competitors * 15)),  # 0 gyms = 100pts, 6+ gyms = 10pts
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