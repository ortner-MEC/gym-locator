"""Idealista API wrapper for Spanish real estate data."""
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
from typing import Dict, Optional, List
from config import IDEALISTA_API_KEY, IDEALISTA_API_SECRET

class IdealistaAPI:
    """Fetches real estate data from Idealista API."""
    
    BASE_URL = 'https://api.idealista.com/3.5/es/search'
    AUTH_URL = 'https://api.idealista.com/oauth/token'
    
    def __init__(self):
        self.access_token = None
        self.api_key = IDEALISTA_API_KEY
        self.api_secret = IDEALISTA_API_SECRET
    
    def _get_access_token(self) -> str:
        """OAuth2 authentication with idealista."""
        if self.access_token:
            return self.access_token
        
        credentials = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = 'grant_type=client_credentials&scope=read'
        
        try:
            req = urllib.request.Request(
                self.AUTH_URL,
                data=data.encode(),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                self.access_token = result['access_token']
                return self.access_token
                
        except Exception as e:
            print(f"Idealista Auth Error: {e}")
            return None
    
    def search_commercial(self, lat: float, lng: float, 
                         radius_m: int = 2000,
                         min_size: int = 200,
                         max_size: int = 800) -> Dict:
        """Search for commercial properties (local/nave) near location."""
        token = self._get_access_token()
        if not token:
            return {'error': 'Authentication failed'}
        
        params = {
            'center': f"{lat},{lng}",
            'distance': radius_m,
            'propertyType': 'premises',  # Commercial premises
            'operation': 'rent',  # For rent
            'minSize': min_size,
            'maxSize': max_size,
            'maxItems': 50,
            'order': 'distance',
            'sort': 'asc'
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{query_string}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Idealista API Error {e.code}: {error_body}")
            return {'error': f'HTTP {e.code}', 'details': error_body}
        except Exception as e:
            print(f"Idealista Request Error: {e}")
            return {'error': str(e)}
    
    def analyze_rental_market(self, lat: float, lng: float) -> Dict:
        """Analyze rental market conditions for gym location."""
        print("\n🏠 Analysiere Mietmarkt (Idealista)...")
        
        # Search for commercial properties
        results = self.search_commercial(lat, lng, radius_m=3000)
        
        if 'error' in results:
            return {
                'available': False,
                'error': results.get('error'),
                'properties': [],
                'average_price_per_m2': 0,
                'market_score': 0
            }
        
        properties = results.get('elementList', [])
        
        if not properties:
            return {
                'available': False,
                'error': 'No commercial properties found',
                'properties': [],
                'average_price_per_m2': 0,
                'market_score': 0
            }
        
        # Calculate average price per m²
        prices_per_m2 = []
        suitable_properties = []
        
        for prop in properties:
            price = prop.get('price', 0)
            size = prop.get('size', 0)
            
            if price > 0 and size > 0:
                price_per_m2 = price / size
                prices_per_m2.append(price_per_m2)
                
                # Check if suitable for gym (350m² range)
                if 250 <= size <= 600:
                    suitable_properties.append({
                        'price': price,
                        'size': size,
                        'price_per_m2': round(price_per_m2, 2),
                        'address': prop.get('address', 'N/A'),
                        'url': prop.get('url', 'N/A'),
                        'distance': prop.get('distance', 0)
                    })
        
        avg_price = sum(prices_per_m2) / len(prices_per_m2) if prices_per_m2 else 0
        
        # Score: Lower price = better (Spain avg ~8-15€/m² for commercial)
        # <8€ = excellent, 8-12€ = good, 12-18€ = moderate, >18€ = expensive
        if avg_price < 8:
            market_score = 100
        elif avg_price < 12:
            market_score = 80
        elif avg_price < 18:
            market_score = 60
        else:
            market_score = 40
        
        return {
            'available': True,
            'properties_found': len(properties),
            'suitable_properties': suitable_properties[:5],  # Top 5
            'average_price_per_m2': round(avg_price, 2),
            'market_score': market_score,
            'market_rating': self._get_market_rating(avg_price),
            'monthly_estimate_350m2': int(avg_price * 350) if avg_price > 0 else 0
        }
    
    def _get_market_rating(self, price_per_m2: float) -> str:
        """Get market rating based on price."""
        if price_per_m2 < 8:
            return '🟢 Günstig'
        elif price_per_m2 < 12:
            return '🟡 Moderat'
        elif price_per_m2 < 18:
            return '🟠 Teuer'
        else:
            return '🔴 Sehr teuer'
    
    def compare_neighborhoods(self, locations: List[Dict]) -> Dict:
        """Compare rental prices across multiple neighborhoods."""
        comparisons = []
        
        for loc in locations:
            result = self.analyze_rental_market(loc['lat'], loc['lng'])
            comparisons.append({
                'name': loc.get('name', 'Unknown'),
                'price_per_m2': result.get('average_price_per_m2', 0),
                'monthly_350m2': result.get('monthly_estimate_350m2', 0),
                'market_score': result.get('market_score', 0),
                'market_rating': result.get('market_rating', 'N/A')
            })
        
        # Sort by price
        comparisons.sort(key=lambda x: x['price_per_m2'])
        
        return {
            'comparisons': comparisons,
            'cheapest': comparisons[0] if comparisons else None,
            'most_expensive': comparisons[-1] if comparisons else None
        }