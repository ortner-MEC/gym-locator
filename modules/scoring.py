"""Scoring algorithm for gym location analysis - SmartGym focused."""
from typing import Dict, List


class LocationScorer:
    """Calculates overall location score focused on what matters for SmartGym."""
    
    @staticmethod
    def calculate_overall_score(analysis_data: Dict) -> Dict:
        """Calculate weighted overall score based on real data."""
        competition = analysis_data.get('competition', {})
        accessibility = analysis_data.get('accessibility', {})
        travel = analysis_data.get('travel_analysis', {})
        rental = analysis_data.get('rental_market', {})
        ine_data = analysis_data.get('ine_demographics', {})
        
        # === COMPETITION SCORE (35%) ===
        # Based on real competitor count and market potential
        market_potential = competition.get('market_potential', 50)
        real_gyms = competition.get('real_count', competition.get('count', 0))
        
        # Fewer real gyms = better score
        if real_gyms == 0:
            comp_score = 95
        elif real_gyms <= 2:
            comp_score = 80
        elif real_gyms <= 4:
            comp_score = 60
        elif real_gyms <= 6:
            comp_score = 40
        else:
            comp_score = max(10, 30 - (real_gyms - 6) * 5)
        
        # Blend with market potential
        comp_score = (comp_score * 0.6) + (market_potential * 0.4)
        
        # === ACCESSIBILITY SCORE (20%) ===
        acc_score = accessibility.get('accessibility_score', 50)
        
        # === REACHABILITY SCORE (25%) ===
        # How many people can reach the gym
        walking = travel.get('walking', {}) if travel else {}
        driving = travel.get('driving', {}) if travel else {}
        
        walk_pop = walking.get('estimated_population_10min', 0)
        drive_pop = driving.get('estimated_population_10min', 0)
        
        # Walking population score (important for daily visits)
        if walk_pop > 10000:
            walk_score = 100
        elif walk_pop > 5000:
            walk_score = 80
        elif walk_pop > 2000:
            walk_score = 60
        elif walk_pop > 1000:
            walk_score = 40
        else:
            walk_score = max(10, walk_pop / 50)
        
        # Driving population (catchment area)
        if drive_pop > 50000:
            drive_score = 100
        elif drive_pop > 30000:
            drive_score = 80
        elif drive_pop > 15000:
            drive_score = 60
        else:
            drive_score = max(10, drive_pop / 300)
        
        reach_score = walk_score * 0.4 + drive_score * 0.6
        
        # === RENTAL SCORE (20%) ===
        avg_rent = rental.get('average_price_sqm', 0) if rental else 0
        if avg_rent > 0:
            # Lower rent = higher score for SmartGym (350m² is a lot of space)
            if avg_rent < 6:
                rent_score = 95
            elif avg_rent < 8:
                rent_score = 80
            elif avg_rent < 10:
                rent_score = 65
            elif avg_rent < 12:
                rent_score = 50
            elif avg_rent < 15:
                rent_score = 35
            else:
                rent_score = 20
        else:
            rent_score = 50  # Neutral if no data
        
        # === WEIGHTED TOTAL ===
        scores = {
            'competition': round(comp_score, 1),
            'accessibility': round(acc_score, 1),
            'reachability': round(reach_score, 1),
            'rental': round(rent_score, 1),
        }
        
        total_score = (
            comp_score * 0.35 +
            acc_score * 0.20 +
            reach_score * 0.25 +
            rent_score * 0.20
        )
        
        # INE demographic bonus (up to +10 points)
        if ine_data and ine_data.get('scores'):
            ine_score = ine_data['scores'].get('overall_demographic_score', 50)
            if ine_score > 60:
                total_score = min(100, total_score + (ine_score - 50) * 0.2)
        
        # Determine rating
        if total_score >= 70:
            rating = '🟢 EXCELLENT'
            recommendation = 'Hoch empfohlen! Sehr gute Bedingungen für SmartGym.'
        elif total_score >= 55:
            rating = '🟡 GUT'
            recommendation = 'Guter Standort. Detailprüfung empfohlen.'
        elif total_score >= 40:
            rating = '🟠 MODERATE'
            recommendation = 'Möglich, aber Risiken beachten.'
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
        risks = []
        
        comp = data.get('competition', {})
        real_count = comp.get('real_count', comp.get('count', 0))
        if real_count >= 5:
            risks.append(f"Hohe Konkurrenz ({real_count} echte Gyms im Umkreis)")
        
        closest = comp.get('closest_competitor')
        if closest and closest.get('distance_km', 99) < 0.3:
            risks.append(f"Gym sehr nah: {closest['name']} ({closest['distance_km']}km)")
        
        travel = data.get('travel_analysis', {})
        walking = travel.get('walking', {}) if travel else {}
        if walking.get('estimated_population_10min', 0) < 2000:
            risks.append("Wenig Fußgänger-Einzugsgebiet (<2.000 in 10min)")
        
        rental = data.get('rental_market', {})
        if rental and rental.get('average_price_sqm', 0) > 12:
            risks.append(f"Hohe Miete: {rental['average_price_sqm']}€/m²")
        
        return risks
    
    @staticmethod
    def _identify_opportunities(data: Dict) -> List[str]:
        opportunities = []
        
        comp = data.get('competition', {})
        real_count = comp.get('real_count', comp.get('count', 0))
        
        if real_count <= 2:
            opportunities.append(f"Wenig Konkurrenz: Nur {real_count} echte Gyms")
        
        people_per_gym = comp.get('people_per_gym')
        if people_per_gym and people_per_gym != 'N/A' and people_per_gym > 5000:
            opportunities.append(f"Unterversorgter Markt: {people_per_gym} Einwohner/Gym")
        
        access = data.get('accessibility', {})
        if access.get('parking_count', 0) >= 10:
            opportunities.append(f"Gute Parksituation ({access['parking_count']} Parkplätze)")
        if access.get('accessibility_score', 0) > 70:
            opportunities.append("Gute Erreichbarkeit (ÖPNV + Parken)")
        
        travel = data.get('travel_analysis', {})
        driving = travel.get('driving', {}) if travel else {}
        if driving.get('estimated_population_10min', 0) > 40000:
            opportunities.append(f"Großes Auto-Einzugsgebiet: {driving['estimated_population_10min']:,} in 10min")
        
        rental = data.get('rental_market', {})
        if rental and rental.get('average_price_sqm', 99) < 8:
            opportunities.append(f"Günstige Miete: {rental['average_price_sqm']}€/m²")
        
        return opportunities
