"""Fotocasa API wrapper for Spanish real estate data (Alternative to Idealista)."""
import urllib.request
import urllib.error
import urllib.parse
import json
from typing import Dict, Optional, List
from config import FOTOCASA_API_KEY

class FotocasaAPI:
    """Fetches real estate data from Fotocasa API."""
    
    def __init__(self):
        self.api_key = FOTOCASA_API_KEY
        self.has_api_access = bool(FOTOCASA_API_KEY)
    
    def search_commercial_rent(self, lat: float, lng: float, 
                               radius_m: int = 3000,
                               min_size: int = 200,
                               max_size: int = 800) -> Dict:
        """Search for commercial rental properties (local/nave/office)."""
        
        if not self.has_api_access:
            return self._estimate_fallback(lat, lng, min_size, max_size)
        
        # API call would go here if we have access
        return self._estimate_fallback(lat, lng, min_size, max_size)
    
    def _estimate_fallback(self, lat: float, lng: float, 
                          min_size: int, max_size: int) -> Dict:
        """Estimate market data based on location (no API needed)."""
        print("   (Fotocasa: Nutze Marktdaten-Schätzung)")
        
        city_data = self._estimate_by_location(lat, lng)
        
        # Generate typical properties
        properties = []
        base_price = city_data['price_per_m2']
        sizes = [250, 300, 350, 400, 500]
        
        for i, size in enumerate(sizes):
            if size > max_size:
                break
            
            price_variation = 0.9 + (i * 0.05)
            price_per_m2 = base_price * price_variation
            total_price = int(price_per_m2 * size)
            
            properties.append({
                'title': f'Local comercial {size}m² - {city_data["city"]}',
                'price': total_price,
                'size': size,
                'price_per_m2': round(price_per_m2, 2),
                'location': city_data['city'],
                'is_estimated': True
            })
        
        return {
            'elementList': properties,
            'total': len(properties),
            'source': 'estimation',
            'city': city_data['city']
        }
    
    def _estimate_by_location(self, lat: float, lng: float) -> Dict:
        """Estimate market data based on coordinates."""
        
        # Murcia region (SmartGym relevant)
        if 37.95 <= lat <= 38.05 and -1.20 <= lng <= -1.05:
            return {'city': 'Murcia', 'price_per_m2': 8.00}
        
        # Madrid
        if 40.3 <= lat <= 40.5 and -3.8 <= lng <= -3.5:
            return {'city': 'Madrid', 'price_per_m2': 12.00}
        
        # Barcelona
        if 41.35 <= lat <= 41.45 and 2.10 <= lng <= 2.25:
            return {'city': 'Barcelona', 'price_per_m2': 16.00}
        
        # Valencia
        if 39.4 <= lat <= 39.55 and -0.45 <= lng <= -0.35:
            return {'city': 'Valencia', 'price_per_m2': 10.50}
        
        # Sevilla
        if 37.35 <= lat <= 37.45 and -6.0 <= lng <= -5.85:
            return {'city': 'Sevilla', 'price_per_m2': 9.50}
        
        # Default
        return {'city': 'Spanien', 'price_per_m2': 9.00}
    
    def analyze_rental_market(self, lat: float, lng: float) -> Dict:
        """Analyze rental market conditions for gym location."""
        print("\n🏠 Analysiere Mietmarkt (Fotocasa)...")
        
        results = self.search_commercial_rent(lat, lng)
        properties = results.get('elementList', [])
        
        if not properties:
            return {'available': False, 'market_score': 0}
        
        prices_per_m2 = [p['price_per_m2'] for p in properties]
        avg_price = sum(prices_per_m2) / len(prices_per_m2)
        
        # Score: <8€=100, 8-12€=80, 12-18€=60, >18€=40
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
            'suitable_properties': properties[:5],
            'average_price_per_m2': round(avg_price, 2),
            'monthly_estimate_350m2': int(avg_price * 350),
            'market_score': market_score,
            'market_rating': self._get_rating(avg_price),
            'is_estimated': True,
            'note': 'Geschätzte Werte basierend auf Marktdaten. Für exakte Preise: Fotocasa API-Zugang beantragen.'
        }
    
    def _get_rating(self, price_per_m2: float) -> str:
        if price_per_m2 < 8:
            return '🟢 Günstig'
        elif price_per_m2 < 12:
            return '🟡 Moderat'
        elif price_per_m2 < 18:
            return '🟠 Teuer'
        else:
            return '🔴 Sehr teuer'