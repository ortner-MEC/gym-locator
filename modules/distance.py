"""Google Distance Matrix API for accessibility analysis."""
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Tuple
from config import GOOGLE_DISTANCE_API_KEY

class DistanceAPI:
    def __init__(self, api_key: str = GOOGLE_DISTANCE_API_KEY):
        self.api_key = api_key
        self.base_url = 'https://maps.googleapis.com/maps/api/distancematrix/json'

    def calculate_reachability(self, origin_lat: float, origin_lng: float, 
                              destinations: List[Tuple[float, float]], 
                              mode: str = 'walking') -> Dict:
        """Calculate how many people can reach the location within X minutes."""
        if not destinations:
            return {'reachable_count': 0, 'average_time': 0}
        
        dest_strings = [f"{lat},{lng}" for lat, lng in destinations[:25]]
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
                return {'reachable_count': 0, 'average_time': 0, 'error': data['status']}
            
            elements = data['rows'][0]['elements']
            
            reachable = 0
            times = []
            for elem in elements:
                if elem['status'] == 'OK':
                    duration_mins = elem['duration']['value'] / 60
                    times.append(duration_mins)
                    if duration_mins <= 15:
                        reachable += 1
            
            return {
                'reachable_count': reachable,
                'average_time': round(sum(times) / len(times), 1) if times else 0,
                'total_checked': len(destinations)
            }
            
        except Exception as e:
            print(f"Error calculating distances: {e}")
            return {'reachable_count': 0, 'average_time': 0, 'error': str(e)}

    def get_drive_times(self, origin_lat: float, origin_lng: float,
                       destinations: List[Tuple[float, float]]) -> Dict:
        """Get driving times to assess car accessibility."""
        return self.calculate_reachability(origin_lat, origin_lng, destinations, mode='driving')