"""Competition intelligence module with AI-based filtering and distance weighting."""
import re
import math
from typing import Dict, List, Tuple

class CompetitionIntelligence:
    """Intelligently filters and categorizes fitness competition with distance weighting."""
    
    # Keywords that indicate NON-fitness facilities
    FALSE_POSITIVE_KEYWORDS = [
        'piscina', 'swimming', 'pool', 'natación', 'schwimmbad',
        'campo', 'field', 'court', 'pista', 'tenis', 'fútbol', 'padel', 'pádel',
        'basketball', 'volleyball', 'futbol', 'football',
        'pabellón', 'pavilion', 'polideportivo', 'sports hall', 'eventos',
        'skate', 'parque', 'park', 'playground', 'stadium', 'estadio'
    ]
    
    # Keywords that indicate REAL fitness competition
    TRUE_GYM_KEYWORDS = [
        'gym', 'gimnasio', 'fitness', 'muscle', 'músculo', 'pesa', 'pesas',
        'weight', 'kraft', 'training', 'entrenamiento', 'crossfit', 'box',
        'fit', 'workout', 'bodybuilding', 'culturismo', 'fitness24', 'mcfit',
        'smart gym', 'functional', 'hiit', 'pilates', 'yoga studio',
        'maquinas', 'máquinas', 'machines', 'cinta', 'correr', 'running',
        'basic-fit', 'basic fit', 'viva gym', 'altafit', 'crosstraining'
    ]
    
    def __init__(self, origin_lat: float = None, origin_lng: float = None):
        self.origin_lat = origin_lat
        self.origin_lng = origin_lng
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters using Haversine formula."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_proximity_score(self, distance_m: float) -> float:
        """Calculate proximity threat score (0-100). Closer = higher threat."""
        if distance_m < 200:  # Less than 200m - very high threat
            return 100
        elif distance_m < 500:  # 200-500m - high threat
            return 80
        elif distance_m < 1000:  # 500m-1km - medium threat
            return 60
        elif distance_m < 1500:  # 1-1.5km - moderate threat
            return 40
        elif distance_m < 2000:  # 1.5-2km - low threat
            return 20
        else:  # Over 2km - minimal threat
            return 10
    
    def analyze_competitor(self, place: Dict) -> Dict:
        """Analyze if a place is real competition for a SmartGym."""
        name = place.get('displayName', {}).get('text', '').lower()
        types = [t.lower() for t in place.get('types', [])]
        
        # Get location for distance calculation
        location = place.get('location', {})
        place_lat = location.get('latitude')
        place_lng = location.get('longitude')
        
        distance_m = None
        proximity_score = 50  # Default medium
        
        if place_lat and place_lng and self.origin_lat and self.origin_lng:
            distance_m = self.calculate_distance(self.origin_lat, self.origin_lng, place_lat, place_lng)
            proximity_score = self.calculate_proximity_score(distance_m)
        
        # Check for false positive indicators
        false_positive_score = self._check_false_positive_indicators(name, types)
        
        # Check for true gym indicators
        true_gym_score = self._check_true_gym_indicators(name, types)
        
        # Determine category
        category = self._categorize_competitor(name, false_positive_score, true_gym_score)
        
        return {
            'name': place.get('displayName', {}).get('text', 'Unbekannt'),
            'rating': place.get('rating', 0),
            'user_ratings': place.get('userRatingCount', 0),
            'types': types,
            'distance_m': distance_m,
            'distance_km': round(distance_m / 1000, 2) if distance_m else None,
            'proximity_score': proximity_score,
            'category': category,
            'false_positive_score': false_positive_score,
            'true_gym_score': true_gym_score,
            'is_real_competition': category in ['direct_competitor', 'indirect_competitor'],
            'relevance': self._calculate_relevance(category, proximity_score)
        }
    
    def _check_false_positive_indicators(self, name: str, types: List[str]) -> int:
        """Check how many false positive indicators match."""
        score = 0
        
        for keyword in self.FALSE_POSITIVE_KEYWORDS:
            if keyword in name:
                score += 2
        
        type_str = ' '.join(types)
        if 'swimming_pool' in type_str or 'aquatic' in type_str:
            score += 3
        if 'stadium' in type_str or 'athletic' in type_str:
            score += 3
        
        return score
    
    def _check_true_gym_indicators(self, name: str, types: List[str]) -> int:
        """Check how many true gym indicators match."""
        score = 0
        
        for keyword in self.TRUE_GYM_KEYWORDS:
            if keyword in name:
                score += 2
        
        type_str = ' '.join(types)
        if 'gym' in type_str or 'fitness' in type_str:
            score += 3
        if 'sports_complex' in type_str:
            score += 1
        
        return score
    
    def _categorize_competitor(self, name: str, false_score: int, true_score: int) -> str:
        """Categorize the competitor based on scores."""
        if false_score >= 3:
            return 'not_competition'
        
        if true_score >= 4:
            return 'direct_competitor'
        
        if true_score >= 2:
            return 'indirect_competitor'
        
        if false_score > true_score:
            return 'not_competition'
        
        return 'unclear'
    
    def _calculate_relevance(self, category: str, proximity_score: float) -> float:
        """Calculate relevance score based on category and proximity."""
        base_weights = {
            'direct_competitor': 100,
            'indirect_competitor': 50,
            'unclear': 25,
            'not_competition': 0
        }
        
        base = base_weights.get(category, 25)
        
        # Adjust by proximity (closer competitors are more relevant)
        if category in ['direct_competitor', 'indirect_competitor']:
            # Weight: 60% category, 40% proximity
            return base * 0.6 + proximity_score * 0.4
        
        return base
    
    def filter_real_competition(self, places: List[Dict]) -> Dict:
        """Filter and categorize all found places with distance analysis."""
        analyzed = []
        
        for place in places:
            analysis = self.analyze_competitor(place)
            analyzed.append(analysis)
        
        # Sort by relevance (distance + category)
        analyzed.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Categorize
        real_competitors = [p for p in analyzed if p['is_real_competition']]
        not_competition = [p for p in analyzed if p['category'] == 'not_competition']
        unclear = [p for p in analyzed if p['category'] == 'unclear']
        
        # Calculate weighted scores based on proximity
        if real_competitors:
            # Weight by proximity: closer gyms hurt more
            weighted_rating = sum(p['rating'] * (p['proximity_score'] / 100) for p in real_competitors if p['rating'])
            weight_sum = sum(p['proximity_score'] / 100 for p in real_competitors if p['rating'])
            avg_rating = weighted_rating / weight_sum if weight_sum > 0 else 0
            
            highly_rated = sum(1 for p in real_competitors if p['rating'] and p['rating'] >= 4.0 and p['proximity_score'] >= 60)
            
            # Calculate average distance
            distances = [p['distance_m'] for p in real_competitors if p['distance_m']]
            avg_distance = sum(distances) / len(distances) if distances else 0
            
            # Closest competitor
            closest = min(real_competitors, key=lambda x: x['distance_m'] if x['distance_m'] else 9999)
        else:
            avg_rating = 0
            highly_rated = 0
            avg_distance = 0
            closest = None
        
        real_count = len(real_competitors)
        
        # NEW: Distance-weighted density score
        # If there's a gym within 200m = critical (score 0)
        # If closest is 500m+ = much better
        if real_count == 0:
            distance_weighted_score = 100
        elif closest and closest['distance_m'] < 200:
            distance_weighted_score = 0  # Gym right next door!
        elif closest and closest['distance_m'] < 500:
            distance_weighted_score = 30
        elif closest and closest['distance_m'] < 1000:
            distance_weighted_score = 60
        else:
            distance_weighted_score = max(0, 100 - (real_count * 10))
        
        return {
            'total_found': len(places),
            'real_competitors': real_competitors,
            'not_competition': not_competition,
            'unclear': unclear,
            'real_count': real_count,
            'average_rating': round(avg_rating, 1),
            'highly_rated_count': highly_rated,
            'avg_distance_m': round(avg_distance, 0) if avg_distance else None,
            'closest_competitor': closest,
            'density_score': distance_weighted_score,
            'market_saturation': 'high' if real_count >= 5 else 'medium' if real_count >= 2 else 'low'
        }
    
    def generate_explanation(self, result: Dict) -> List[str]:
        """Generate human-readable explanation of filtering and distance analysis."""
        explanations = []
        
        total = result['total_found']
        real = result['real_count']
        not_comp = len(result['not_competition'])
        
        explanations.append(f"Von {total} gefundenen Einrichtungen sind {real} echte Konkurrenz")
        
        if not_comp > 0:
            examples = [p['name'] for p in result['not_competition'][:3]]
            explanations.append(f"Ausgeschlossen: {', '.join(examples)} etc.")
        
        if result.get('closest_competitor'):
            closest = result['closest_competitor']
            dist_km = closest['distance_km']
            explanations.append(f"Nächster Konkurrent: {closest['name']} ({dist_km}km entfernt)")
        
        if result.get('avg_distance_m'):
            avg_km = result['avg_distance_m'] / 1000
            explanations.append(f"Durchschnittsentfernung: {avg_km:.1f}km")
        
        return explanations