"""INE API with postal code (Código Postal) level data."""
import urllib.request
import urllib.error
import json
from typing import Dict, Optional
from datetime import datetime

class INEPostalCodeAPI:
    """Fetches demographic data at postal code level from INE."""
    
    BASE_URL = 'https://servicios.ine.es/wstempus/js/ES/DATOS'
    
    def __init__(self):
        self.cache = {}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to INE API."""
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            query = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query}"
        
        try:
            req = urllib.request.Request(url, headers={
                'Accept': 'application/json',
                'User-Agent': 'SmartGym-Analyzer/1.0'
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {}
    
    def get_postal_code_data(self, postal_code: str, city_hint: str = None) -> Dict:
        """Get demographic data for specific postal code."""
        print(f"\n📮 Suche INE-Daten für Postleitzahl: {postal_code}")
        
        if not postal_code or len(postal_code) != 5:
            print(f"   ⚠️ Ungültige PLZ: {postal_code}")
            return self._empty_postal_result(postal_code)
        
        # INE has data by municipality, not directly by postal code
        # We need to map postal code to municipality first
        # For now, we use the city hint or fallback to city-level data
        
        # Try to get municipality stats if we have a city hint
        if city_hint:
            from modules.ine_api import INEAPI
            city_api = INEAPI()
            city_data = city_api.analyze_location(city_hint)
            
            # Adjust for postal code (urban postal codes typically have higher density)
            adjusted = self._adjust_for_postal_code(city_data, postal_code)
            return adjusted
        
        return self._empty_postal_result(postal_code)
    
    def _adjust_for_postal_code(self, city_data: Dict, postal_code: str) -> Dict:
        """Adjust city data for postal code level (rough estimation)."""
        base_demo = city_data.get('demographics', {})
        base_scores = city_data.get('scores', {})
        
        # First 2 digits indicate province/autonomous community
        province_code = postal_code[:2]
        
        # Urban postal codes (in big cities) have different characteristics
        urban_provinces = {
            '28': 'Madrid', '08': 'Barcelona', '46': 'Valencia',
            '41': 'Sevilla', '15': 'A Coruña', '50': 'Zaragoza',
            '18': 'Granada', '29': 'Málaga', '05': 'Ávila'
        }
        
        is_urban = province_code in urban_provinces
        
        # Adjust population density for urban areas
        density_multiplier = 2.5 if is_urban else 1.0
        base_pop = base_demo.get('total_population', 0)
        adjusted_pop = int(base_pop * density_multiplier * 0.02)  # PC is ~2% of city
        
        # Postal codes ending in 0,1,2 are usually central/business districts
        last_digit = int(postal_code[-1])
        is_central = last_digit in [0, 1, 2]
        business_multiplier = 1.3 if is_central else 0.9
        
        # Adjust young percentage (central areas often have more young professionals)
        young_pct = base_demo.get('young_percentage', 15)
        adjusted_young = min(40, young_pct * (1.2 if is_central else 0.95))
        
        # Income index (central areas often wealthier)
        income = base_demo.get('income_index', 100)
        adjusted_income = income * (1.15 if is_central else 1.0)
        
        return {
            'postal_code': postal_code,
            'province': urban_provinces.get(province_code, 'Unknown'),
            'is_urban': is_urban,
            'is_central': is_central,
            'demographics': {
                'estimated_population': adjusted_pop,
                'young_percentage': round(adjusted_young, 1),
                'income_index': round(adjusted_income, 1)
            },
            'city_reference': city_data.get('city'),
            'data_quality': 'estimated_from_city_data',
            'notes': f"PLZ-Daten basieren auf Hochrechnung aus Stadtdaten ({city_data.get('city', 'N/A')}). Für präzise PLZ-Daten direkter INE-Zugriff nötig."
        }
    
    def _empty_postal_result(self, postal_code: str) -> Dict:
        """Return empty result structure."""
        return {
            'postal_code': postal_code,
            'demographics': {},
            'city_reference': None,
            'data_quality': 'unavailable',
            'notes': 'Keine PLZ-spezifischen Daten verfügbar'
        }
    
    def compare_postal_codes(self, postal_codes: List[str], city: str) -> Dict:
        """Compare multiple postal codes in same city."""
        results = []
        
        for pc in postal_codes:
            data = self.get_postal_code_data(pc, city)
            demo = data.get('demographics', {})
            
            results.append({
                'postal_code': pc,
                'population': demo.get('estimated_population', 0),
                'young_percentage': demo.get('young_percentage', 0),
                'income_index': demo.get('income_index', 100),
                'is_central': data.get('is_central', False)
            })
        
        # Rank by overall attractiveness (young population + income)
        for r in results:
            r['attractiveness_score'] = (
                r['young_percentage'] * 2 + 
                (r['income_index'] - 100) * 0.5 +
                (2 if r['is_central'] else 0)
            )
        
        results.sort(key=lambda x: x['attractiveness_score'], reverse=True)
        
        return {
            'comparisons': results,
            'best_postal_code': results[0]['postal_code'] if results else None,
            'city': city
        }