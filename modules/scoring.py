"""Scoring algorithm for gym location analysis."""
from config import WEIGHTS
from typing import Dict, List

class LocationScorer:
    """Calculates overall location score based on multiple factors."""
    
    @staticmethod
    def calculate_overall_score(analysis_data: Dict) -> Dict:
        """Calculate weighted overall score."""
        competition = analysis_data.get('competition', {})
        demographics = analysis_data.get('demographics', {})
        accessibility = analysis_data.get('accessibility', {})
        travel = analysis_data.get('travel_analysis', {})
        ine_data = analysis_data.get('ine_demographics', {})
        postal = analysis_data.get('postal_code_data', {})
        
        # Individual scores (0-100)
        scores = {
            'competition': competition.get('density_score', 50),
            'demographics': demographics.get('demographic_score', 50),
            'accessibility': accessibility.get('accessibility_score', 50),
            'market_saturation': 100 - min(100, competition.get('count', 0) * 10),
            'reachability': travel.get('score', 50) if travel else 50,
        }
        
        # Enhanced weighing with reachability
        total_score = (
            scores['competition'] * 0.25 +
            scores['demographics'] * 0.20 +
            scores['accessibility'] * 0.20 +
            scores['market_saturation'] * 0.15 +
            scores['reachability'] * 0.20  # NEW: 20% for reachability
        )
        
        # INE demographic bonus
        if ine_data and ine_data.get('scores'):
            ine_score = ine_data['scores'].get('overall_demographic_score', 50)
            total_score = total_score * 0.8 + ine_score * 0.2
        
        # Postal code boost for central areas
        if postal and postal.get('is_central'):
            total_score = min(100, total_score + 5)
        
        # Determine rating
        if total_score >= 75:
            rating = '🟢 EXCELLENT'
            recommendation = 'Hoch empfohlen! Optimale Bedingungen für SmartGym.'
        elif total_score >= 50:
            rating = '🟡 MODERATE'
            recommendation = 'Möglich, aber mit Vorsicht. Prüfe genauere Details.'
        else:
            rating = '🔴 RISKY'
            recommendation = 'Nicht empfohlen. Zu viele Risikofaktoren.'
        
        return {
            'total_score': round(total_score, 1),
            'individual_scores': scores,
            'rating': rating,
            'recommendation': recommendation,
            'risk_factors': LocationScorer._identify_risks(analysis_data),
            'opportunities': LocationScorer._identify_opportunities(analysis_data)
        }
    
    @staticmethod
    def _identify_risks(data: Dict) -> List[str]:
        """Identify potential risks for this location."""
        risks = []
        
        comp = data.get('competition', {})
        if comp.get('count', 0) >= 5:
            risks.append(f"Hohe Konkurrenz ({comp['count']} Gyms im Umkreis)")
        if comp.get('highly_rated_count', 0) >= 2:
            risks.append("Starke Konkurrenz: Mehrere gut bewertete Gyms")
        
        demo = data.get('demographics', {})
        if demo.get('demographic_score', 0) < 40:
            risks.append("Geringe Zielgruppen-Dichte in der Umgebung")
        
        access = data.get('accessibility', {})
        if access.get('public_transport_count', 0) < 2:
            risks.append("Schlechte ÖPNV-Anbindung")
        
        # NEW: Reachability risk
        travel = data.get('travel_analysis', {})
        walking = travel.get('walking', {}) if travel else {}
        if walking.get('10min_reach', 0) < 20:
            risks.append("Geringe Reichweite: Wenig Gebiete in 10min zu Fuß erreichbar")
        
        return risks
    
    @staticmethod
    def _identify_opportunities(data: Dict) -> List[str]:
        """Identify opportunities for this location."""
        opportunities = []
        
        comp = data.get('competition', {})
        if comp.get('count', 0) == 0:
            opportunities.append("Keine direkte Konkurrenz – Blue Ocean!")
        if comp.get('average_rating', 5) < 3.5:
            opportunities.append("Schwache Konkurrenz – Chance für besseren Service")
        
        demo = data.get('demographics', {})
        if demo.get('young_count', 0) >= 3:
            opportunities.append("Hohe Studenten-Dichte – ideale Zielgruppe")
        if demo.get('office_count', 0) >= 5:
            opportunities.append("Viele Büros – Potential für Business-Mitgliedschaften")
        
        access = data.get('accessibility', {})
        if access.get('accessibility_score', 0) > 70:
            opportunities.append("Ausgezeichnete Erreichbarkeit")
        
        # NEW: Reachability opportunities
        travel = data.get('travel_analysis', {})
        walking = travel.get('walking', {}) if travel else {}
        if walking.get('10min_reach', 0) > 80:
            opportunities.append(f"Exzellente Fußgängerreichweite: {walking.get('estimated_population_10min', 0):,} Menschen in 10min")
        
        # INE demographic bonus
        ine = data.get('ine_demographics', {})
        if ine and ine.get('demographics', {}).get('young_percentage', 0) > 30:
            opportunities.append(f"High-value Zielgruppe: {ine['demographics']['young_percentage']}% der Bevölkerung sind 20-39")
        
        # Postal code
        postal = data.get('postal_code_data', {})
        if postal and postal.get('is_central'):
            opportunities.append("Zentrale Lage: Hohe Fußgängerfrequenz")
        
        return opportunities