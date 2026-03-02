"""Enhanced competition intelligence with realistic filtering for SmartGym locations."""
import re
import math
from typing import Dict, List

class CompetitionIntelligence:
    """
    Intelligently filters fitness competition specifically for SmartGym business model.
    
    SmartGym target: 24/7 automated gyms with full equipment (weights, cardio, functional)
    NOT competition: Yoga studios, boxing clubs, niche fitness, small personal training studios
    """
    
    # HIGH PRIORITY - Real competition (full-service gyms)
    TRUE_GYM_KEYWORDS = [
        # Core gym terms
        'gym', 'gimnasio', 'fitness', 'mcfit', 'basic-fit', 'basic fit', 'viva gym',
        'smart gym', 'functional', 'crossfit', 'box', 'boxing gym',
        # Equipment-focused
        'pesas', 'máquinas', 'maquinas', 'kraft', 'krafttraining',
        'cardio', 'cinta', 'correr', 'running', 'weights',
        # 24/7 indicators
        '24h', '24 h', '24/7', '24 7', 'automático', 'automatico',
        # Size indicators
        'fitness park', 'fitnesspark', 'o2 wellness', 'metropolitan',
        # Chain gyms in Spain
        'altafit', 'sports club', 'club deportivo'
    ]
    
    # NEGATIVE - Definitely NOT competition for SmartGym
    FALSE_POSITIVE_KEYWORDS = [
        # Yoga/Pilates/Mind-Body (different target group)
        'yoga', 'pilates', 'meditación', 'meditation', 'mindfulness',
        # Combat sports (different market)
        'boxeo', 'kickboxing', 'mma', 'jiu jitsu', 'judo', 'karate', 'taekwondo',
        # Dance studios
        'danza', 'baile', 'dance', 'zumba studio', 'salsa',
        # Swimming pools
        'piscina', 'piscinas', 'swimming', 'pool', 'natación', 'natacion',
        # Sports facilities (not gyms)
        'pabellón', 'pabellon', 'pavilion', 'polideportivo', 'sports hall',
        'estadio', 'stadium', 'campo', 'field', 'court', 'pista',
        # Outdoor/Specific
        'skate', 'skatepark', 'parque', 'park', 'playground',
        # Small niches
        'personal trainer', 'entrenador personal', 'studio', 'boutique',
        'fisioterapia', 'physio', 'masajes', 'massage', 'wellness center',
        # Children/Seniors specific
        'infantil', 'children', 'kids', 'senior', 'mayores',
        # Rehabilitation
        'rehabilitación', 'rehab', 'fisio', 'physiotherapy'
    ]
    
    def __init__(self, origin_lat: float = None, origin_lng: float = None):
        self.origin_lat = origin_lat
        self.origin_lng = origin_lng
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def analyze_competitor(self, place: Dict) -> Dict:
        """Analyze if a place is real SmartGym competition."""
        name = place.get('displayName', {}).get('text', '').lower()
        types = [t.lower() for t in place.get('types', [])]
        review_count = place.get('userRatingCount', 0)
        
        # Get location
        location = place.get('location', {})
        place_lat = location.get('latitude')
        place_lng = location.get('longitude')
        
        distance_m = None
        if place_lat and place_lng and self.origin_lat and self.origin_lng:
            distance_m = self.calculate_distance(self.origin_lat, self.origin_lng, place_lat, place_lng)
        
        # Scoring
        gym_score = self._score_gym_indicators(name, types, review_count)
        false_score = self._score_false_indicators(name)
        
        # Categorization
        category = self._categorize(gym_score, false_score, review_count, name)
        
        return {
            'name': place.get('displayName', {}).get('text', 'Unbekannt'),
            'rating': place.get('rating', 0),
            'review_count': review_count,
            'distance_m': distance_m,
            'distance_km': round(distance_m / 1000, 2) if distance_m else None,
            'category': category,
            'gym_score': gym_score,
            'false_score': false_score,
            'is_real_competition': category == 'direct_competitor'
        }
    
    def _score_gym_indicators(self, name: str, types: List[str], review_count: int) -> int:
        """Score how likely this is a real gym."""
        score = 0
        
        # Name keywords
        for keyword in self.TRUE_GYM_KEYWORDS:
            if keyword in name:
                score += 3
        
        # Review count as proxy for size (big gyms have more reviews)
        if review_count > 200:
            score += 3  # Big established gym
        elif review_count > 50:
            score += 1  # Medium gym
        elif review_count < 10:
            score -= 2  # Probably small/new studio
        
        return score
    
    def _score_false_indicators(self, name: str) -> int:
        """Score false positive indicators."""
        score = 0
        
        for keyword in self.FALSE_POSITIVE_KEYWORDS:
            if keyword in name:
                score += 5  # High penalty for false positives
        
        return score
    
    def _categorize(self, gym_score: int, false_score: int, review_count: int, name: str) -> str:
        """Categorize based on scores."""
        # Definitely not a gym
        if false_score >= 5:
            return 'not_competition'
        
        # Strong gym indicators + decent size
        if gym_score >= 6 and review_count >= 30:
            return 'direct_competitor'
        
        # Medium indicators
        if gym_score >= 3:
            return 'possible_competitor'
        
        # Too small or unclear
        if review_count < 20 and gym_score < 3:
            return 'not_competition'
        
        return 'unclear'
    
    def filter_real_competition(self, places: List[Dict], population: int = 20000) -> Dict:
        """Filter places and calculate realistic market metrics."""
        analyzed = []
        
        for place in places:
            analysis = self.analyze_competitor(place)
            analyzed.append(analysis)
        
        # Sort by relevance
        analyzed.sort(key=lambda x: (x['is_real_competition'], x.get('review_count', 0)), reverse=True)
        
        # Categorize
        real_competitors = [p for p in analyzed if p['is_real_competition']]
        not_competition = [p for p in analyzed if p['category'] == 'not_competition']
        possible = [p for p in analyzed if p['category'] == 'possible_competitor']
        
        # Realistic population estimate for 2km radius in Spanish coastal town
        # San Pedro del Pinatar: ~25,000 total, ~15,000 in 2km of center
        if not population:
            population = 15000
        
        real_count = len(real_competitors)
        
        # Calculate metrics
        if real_count > 0:
            avg_rating = sum(p['rating'] for p in real_competitors if p['rating']) / len([p for p in real_competitors if p['rating']])
            distances = [p['distance_m'] for p in real_competitors if p['distance_m']]
            avg_distance = sum(distances) / len(distances) if distances else 0
            closest = min(real_competitors, key=lambda x: x['distance_m'] if x['distance_m'] else 9999)
            
            # Count good gyms (4+ stars)
            good_gyms = [p for p in real_competitors if p['rating'] and p['rating'] >= 4.0]
        else:
            avg_rating = 0
            avg_distance = 0
            closest = None
            good_gyms = []
        
        # Market saturation calculation
        people_per_gym = population / real_count if real_count > 0 else float('inf')
        
        # SmartGym target: 600 members
        # Market potential based on people per gym
        if real_count == 0:
            market_potential = 100
            saturation = 'none'
        elif people_per_gym > 8000:
            market_potential = 90
            saturation = 'low'
        elif people_per_gym > 5000:
            market_potential = 70
            saturation = 'medium'
        elif people_per_gym > 3000:
            market_potential = 50
            saturation = 'high'
        else:
            market_potential = 20
            saturation = 'oversaturated'
        
        return {
            'total_found': len(places),
            'real_competitors': real_competitors,
            'real_count': real_count,
            'possible_competitors': possible,
            'not_competition': not_competition,
            'average_rating': round(avg_rating, 1) if real_count > 0 else 0,
            'good_gyms_count': len(good_gyms),
            'closest_competitor': closest,
            'avg_distance_m': round(avg_distance, 0) if avg_distance else None,
            'population_estimate': population,
            'people_per_gym': int(people_per_gym) if people_per_gym != float('inf') else 'N/A',
            'market_potential': market_potential,
            'saturation': saturation
        }
    
    def generate_explanation(self, result: Dict) -> List[str]:
        """Generate human-readable summary."""
        explanations = []
        
        real = result['real_count']
        total = result['total_found']
        filtered = total - real - len(result.get('possible_competitors', []))
        
        explanations.append(f"Von {total} Einträgen: {real} echte Gyms, {filtered} ausgeschlossen (Yoga, Boxen, etc.)")
        
        if result.get('closest_competitor'):
            c = result['closest_competitor']
            explanations.append(f"Nächstes Gym: {c['name']} ({c['distance_km']}km)")
        
        if result.get('people_per_gym') != 'N/A':
            explanations.append(f"{result['people_per_gym']} Einwohner pro Gym")
        
        return explanations