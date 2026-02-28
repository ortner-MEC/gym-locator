"""INE (Instituto Nacional de Estadística) API wrapper for Spanish demographic data."""
import urllib.request
import urllib.error
import json
from typing import Dict, Optional, List
from datetime import datetime

BASE_URL = 'https://servicios.ine.es/wstempus/js/ES/DATOS'

class INEAPI:
    """Fetches demographic data from Spanish National Statistics Institute."""
    
    def __init__(self):
        self.cache = {}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to INE API."""
        url = f"{BASE_URL}{endpoint}"
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
            print(f"INE API Error: {e}")
            return {}
    
    def get_municipality_by_name(self, city: str) -> Optional[str]:
        """Find municipality code by city name."""
        endpoint = f"/NOMBRE/{city.upper()}"
        data = self._make_request(endpoint)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return None
        
        # Get first match
        return str(data[0].get('cod', ''))
    
    def get_population_data(self, municipality_code: str) -> Dict:
        """Get population data for municipality."""
        # Series codes for population data
        # Different series for different age groups
        
        series_total = self._get_series_data('2852', municipality_code)  # Total population
        series_young = self._get_series_data('2853', municipality_code)  # 20-39 years
        series_income = self._get_series_data('7586', municipality_code)  # Income index
        
        total_pop = self._extract_latest_value(series_total)
        young_pop = self._extract_latest_value(series_young)
        income_idx = self._extract_latest_value(series_income)
        
        young_percentage = (young_pop / total_pop * 100) if total_pop > 0 else 0
        
        return {
            'total_population': total_pop,
            'population_young_20_39': young_pop,
            'young_percentage': round(young_percentage, 1),
            'income_index': income_idx or 100,  # 100 = national average
            'municipality_code': municipality_code,
            'year': self._extract_year(series_total)
        }
    
    def _get_series_data(self, series_id: str, municipality_code: str) -> Dict:
        """Fetch specific data series for municipality."""
        # Filter: CO = Municipio
        endpoint = f"/SERIE/{series_id}"
        params = {
            'nult': '1',  # Last value only
            'tv': '15',   # Periodicidad (anual)
        }
        
        data = self._make_request(endpoint, params)
        return data
    
    def _extract_latest_value(self, data: Dict) -> int:
        """Extract latest numeric value from series data."""
        if not data or 'Data' not in data:
            return 0
        
        values = data.get('Data', [])
        if not values:
            return 0
        
        # Get most recent
        latest = values[0]
        return int(latest.get('Valor', 0))
    
    def _extract_year(self, data: Dict) -> int:
        """Extract year from series data."""
        if not data or 'Data' not in data:
            return datetime.now().year
        
        values = data.get('Data', [])
        if not values:
            return datetime.now().year
        
        return int(values[0].get('Anyo', datetime.now().year))
    
    def analyze_location(self, city: str) -> Dict:
        """Complete demographic analysis for a city/municipality."""
        print(f"\n🇪🇸 Frage INE-Daten ab für: {city}")
        
        # Get municipality code
        muni_code = self.get_municipality_by_name(city)
        if not muni_code:
            print(f"   ⚠️ Stadt '{city}' nicht in INE-Datenbank gefunden")
            return self._empty_result()
        
        print(f"   Municipality Code: {muni_code}")
        
        # Get population data
        pop_data = self.get_population_data(muni_code)
        
        # Calculate scores
        scores = self._calculate_scores(pop_data)
        
        return {
            'city': city,
            'municipality_code': muni_code,
            'demographics': pop_data,
            'scores': scores,
            'data_source': 'INE (Instituto Nacional de Estadística)',
            'year': pop_data.get('year', datetime.now().year)
        }
    
    def _calculate_scores(self, data: Dict) -> Dict:
        """Calculate demographic suitability scores."""
        young_pct = data.get('young_percentage', 0)
        income_idx = data.get('income_index', 100)
        total_pop = data.get('total_population', 0)
        
        # Score 0-100 for target group (20-39)
        # 30% young population = excellent (100 pts), <10% = bad (0 pts)
        young_score = min(100, max(0, (young_pct - 10) * 5))
        
        # Income score: 100 = average, >120 = wealthy area (good)
        income_score = min(100, max(0, (income_idx - 80) * 1.25))
        
        # Population density score (larger cities = more potential)
        if total_pop > 100000:
            density_score = 100
        elif total_pop > 50000:
            density_score = 80
        elif total_pop > 20000:
            density_score = 60
        else:
            density_score = 40
        
        overall = (young_score * 0.4 + income_score * 0.35 + density_score * 0.25)
        
        return {
            'target_group_score': round(young_score, 1),  # 20-39 age
            'purchasing_power_score': round(income_score, 1),  # Income
            'market_size_score': round(density_score, 1),  # Total population
            'overall_demographic_score': round(overall, 1)
        }
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'city': None,
            'municipality_code': None,
            'demographics': {},
            'scores': {
                'target_group_score': 0,
                'purchasing_power_score': 0,
                'market_size_score': 0,
                'overall_demographic_score': 0
            },
            'data_source': 'INE (not found)',
            'year': datetime.now().year
        }
    
    def get_comparison_cities(self, main_city: str) -> List[Dict]:
        """Get data for comparison cities (Madrid, Barcelona, Valencia, Sevilla)."""
        comparisons = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla']
        results = []
        
        for city in comparisons:
            if city.lower() != main_city.lower():
                data = self.analyze_location(city)
                results.append(data)
        
        return results