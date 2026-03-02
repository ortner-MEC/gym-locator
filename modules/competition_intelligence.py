"""Competition intelligence module with AI-based filtering."""
import re
from typing import Dict, List

class CompetitionIntelligence:
    """Intelligently filters and categorizes fitness competition."""
    
    # Keywords that indicate NON-fitness facilities
    FALSE_POSITIVE_KEYWORDS = [
        # Swimming pools
        'piscina', 'swimming', 'pool', 'natación', 'schwimmbad',
        # Sports fields/courts
        'campo', 'field', 'court', 'pista', 'tenis', 'fútbol', 'padel', 'pádel',
        'basketball', 'volleyball', 'futbol', 'football',
        # Event venues
        'pabellón', 'pavilion', 'polideportivo', 'sports hall', 'eventos',
        # Other
        'skate', 'parque', 'park', 'playground', 'stadium', 'estadio'
    ]
    
    # Keywords that indicate REAL fitness competition
    TRUE_GYM_KEYWORDS = [
        # Gym types
        'gym', 'gimnasio', 'fitness', 'muscle', 'músculo', 'pesa', 'pesas',
        'weight', 'kraft', 'training', 'entrenamiento', 'crossfit', 'box',
        'fit', 'workout', 'bodybuilding', 'culturismo', 'fitness24', 'mcfit',
        'smart gym', 'functional', 'hiit', 'pilates', 'yoga studio',
        # Equipment references
        'maquinas', 'máquinas', 'machines', 'cinta', 'correr', 'running',
        # Brand indicators
        'basic-fit', 'basic fit', 'viva gym', 'altafit', 'crosstraining'
    ]
    
    # Activity types that suggest it's a gym
    VALID_GYM_TYPES = [
        'gym', 'fitness_center', 'sports_complex',  # Complex can be valid if not filtered by name
        'health_club', 'wellness_center'
    ]
    
    def analyze_competitor(self, place: Dict) -> Dict:
        """Analyze if a place is real competition for a SmartGym."""
        name = place.get('displayName', {}).get('text', '').lower()
        types = [t.lower() for t in place.get('types', [])]
        
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
            'category': category,
            'false_positive_score': false_positive_score,
            'true_gym_score': true_gym_score,
            'is_real_competition': category in ['direct_competitor', 'indirect_competitor'],
            'relevance': self._calculate_relevance(category)
        }
    
    def _check_false_positive_indicators(self, name: str, types: List[str]) -> int:
        """Check how many false positive indicators match."""
        score = 0
        
        # Check name
        for keyword in self.FALSE_POSITIVE_KEYWORDS:
            if keyword in name:
                score += 2
        
        # Check types
        type_str = ' '.join(types)
        if 'swimming_pool' in type_str or 'aquatic' in type_str:
            score += 3
        if 'stadium' in type_str or 'athletic' in type_str:
            score += 3
        
        return score
    
    def _check_true_gym_indicators(self, name: str, types: List[str]) -> int:
        """Check how many true gym indicators match."""
        score = 0
        
        # Check name
        for keyword in self.TRUE_GYM_KEYWORDS:
            if keyword in name:
                score += 2
        
        # Check types
        type_str = ' '.join(types)
        if 'gym' in type_str or 'fitness' in type_str:
            score += 3
        if 'sports_complex' in type_str:
            score += 1  # Could be gym, could be multi-sport
        
        return score
    
    def _categorize_competitor(self, name: str, false_score: int, true_score: int) -> str:
        """Categorize the competitor based on scores."""
        # Strong false positive indicators
        if false_score >= 3:
            return 'not_competition'
        
        # Strong gym indicators
        if true_score >= 4:
            return 'direct_competitor'
        
        # Moderate gym indicators
        if true_score >= 2:
            return 'indirect_competitor'
        
        # Neutral - needs manual review
        if false_score > true_score:
            return 'not_competition'
        
        return 'unclear'
    
    def _calculate_relevance(self, category: str) -> int:
        """Calculate relevance score for weighting."""
        weights = {
            'direct_competitor': 100,
            'indirect_competitor': 50,
            'unclear': 25,
            'not_competition': 0
        }
        return weights.get(category, 25)
    
    def filter_real_competition(self, places: List[Dict]) -> Dict:
        """Filter and categorize all found places."""
        analyzed = []
        
        for place in places:
            analysis = self.analyze_competitor(place)
            analyzed.append(analysis)
        
        # Sort by relevance
        analyzed.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Categorize
        real_competitors = [p for p in analyzed if p['is_real_competition']]
        not_competition = [p for p in analyzed if p['category'] == 'not_competition']
        unclear = [p for p in analyzed if p['category'] == 'unclear']
        
        # Calculate weighted score
        if real_competitors:
            avg_rating = sum(p['rating'] for p in real_competitors if p['rating']) / len([p for p in real_competitors if p['rating']])
            highly_rated = sum(1 for p in real_competitors if p['rating'] and p['rating'] >= 4.0)
        else:
            avg_rating = 0
            highly_rated = 0
        
        # Adjust density score based on REAL competitors only
        real_count = len(real_competitors)
        density_score = max(0, 100 - (real_count * 15)) if real_count <= 6 else 10
        
        return {
            'total_found': len(places),
            'real_competitors': real_competitors,
            'not_competition': not_competition,
            'unclear': unclear,
            'real_count': real_count,
            'average_rating': round(avg_rating, 1),
            'highly_rated_count': highly_rated,
            'density_score': density_score,
            'market_saturation': 'high' if real_count >= 5 else 'medium' if real_count >= 2 else 'low'
        }
    
    def generate_explanation(self, result: Dict) -> List[str]:
        """Generate human-readable explanation of filtering."""
        explanations = []
        
        total = result['total_found']
        real = result['real_count']
        not_comp = len(result['not_competition'])
        
        explanations.append(f"Von {total} gefundenen Einrichtungen sind {real} echte Konkurrenz")
        
        if not_comp > 0:
            examples = [p['name'] for p in result['not_competition'][:3]]
            explanations.append(f"Ausgeschlossen: {', '.join(examples)} etc.")
        
        if result['unclear']:
            explanations.append(f"{len(result['unclear'])} Einträge unklar - manuelle Prüfung empfohlen")
        
        return explanations