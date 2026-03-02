"""Report generation for gym location analysis."""
import json
import os
from datetime import datetime
from typing import Dict
from config import OUTPUT_DIR

class ReportGenerator:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def generate_console_report(self, address: str, analysis_data: Dict, score_data: Dict):
        """Print formatted report to console."""
        print("\n" + "=" * 70)
        print("🏋️  SMARTGYM STANDORT-ANALYSE".center(70))
        print("=" * 70)
        print(f"\n📍 Adresse: {address}")
        print(f"📅 Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        print(f"📐 Suchradius: 2km")
        print("\n" + "-" * 70)
        
        # Overall Score
        print(f"\n📊 GESAMTBEWERTUNG: {score_data['rating']}")
        print(f"   Score: {score_data['total_score']}/100 Punkte")
        print(f"\n💡 Empfehlung: {score_data['recommendation']}")
        
        # Individual Scores
        print("\n" + "-" * 70)
        print("DETAILSCORES:")
        scores = score_data['individual_scores']
        print(f"   🏆 Konkurrenz-Dichte:      {scores['competition']}/100")
        print(f"   👥 Zielgruppen-Score:      {scores['demographics']}/100")
        print(f"   🚗 Erreichbarkeit:         {scores['accessibility']}/100")
        print(f"   📈 Markt-Sättigung:        {scores['market_saturation']}/100")
        print(f"   ⏱️  Reichweite (Fahrzeit): {scores['reachability']}/100")
        
        # Competition Details with intelligent filtering
        comp = analysis_data.get('competition', {})
        print("\n" + "-" * 70)
        print(f"🏢 KONKURRENZANALYSE (KI-gefiltert):")
        
        if comp.get('filtering_explanation'):
            print(f"   📊 {comp['filtering_explanation'][0]}")
            if len(comp['filtering_explanation']) > 1:
                print(f"   ℹ️  {comp['filtering_explanation'][1]}")
        
        print(f"   Gefundene Einrichtungen: {comp.get('total_found', 0)}")
        print(f"   Davon echte Konkurrenz: {comp.get('count', 0)}")
        print(f"   Durchschnittsbewertung: {comp.get('average_rating', 0)}/5.0")
        print(f"   Gut bewertete Gyms (≥4★): {comp.get('highly_rated_count', 0)}")
        print(f"   Marktsättigung: {comp.get('market_saturation', 'unbekannt').upper()}")
        
        if comp.get('competitors'):
            print("\n   🏋️ Echte Konkurrenten:")
            for gym in comp['competitors'][:5]:
                name = gym.get('name', 'Unbekannt')
                rating = gym.get('rating', '-')
                category = gym.get('category', 'unclear')
                cat_emoji = {'direct_competitor': '🎯', 'indirect_competitor': '⚡'}.get(category, '❓')
                print(f"      {cat_emoji} {name} ({rating}★)")
        
        if comp.get('filtered_out'):
            print("\n   ❌ Ausgeschlossen (keine direkte Konkurrenz):")
            for item in comp['filtered_out'][:3]:
                name = item.get('name', 'Unbekannt')
                print(f"      • {name}")
        
        # NEW: Travel Time Analysis
        travel = analysis_data.get('travel_analysis', {})
        if travel:
            print("\n" + "-" * 70)
            print(f"⏱️  FAHRZEIT-ISOCHRONEN:")
            
            walking = travel.get('walking', {})
            if walking:
                print(f"\n   ZU FUSS erreichbar:")
                print(f"      5 Minuten:  {walking.get('5min_reach', 0)} Zonen")
                print(f"      10 Minuten: {walking.get('10min_reach', 0)} Zonen")
                print(f"      15 Minuten: {walking.get('15min_reach', 0)} Zonen")
                print(f"      ↳ Geschätzte Bevölkerung (10min): {walking.get('estimated_population_10min', 0):,}")
                print(f"      ↳ Abdeckung: {walking.get('coverage_percentage', 0)}%")
            
            driving = travel.get('driving', {})
            if driving:
                print(f"\n   MIT AUTO erreichbar:")
                print(f"      5 Minuten:  {driving.get('5min_reach', 0)} Zonen")
                print(f"      10 Minuten: {driving.get('10min_reach', 0)} Zonen")
                print(f"      ↳ Geschätzte Bevölkerung (10min): {driving.get('estimated_population_10min', 0):,}")
        
        # Google Demographics
        demo = analysis_data.get('demographics', {})
        print("\n" + "-" * 70)
        print(f"👥 ZIELGRUPPEN-ANALYSE (Google Places):")
        print(f"   Wohngebiete:     {demo.get('residential_count', 0)}")
        print(f"   Bürogebäude:     {demo.get('office_count', 0)}")
        print(f"   Bildungseinrichtungen: {demo.get('young_count', 0)}")
        print(f"   Primäre Zielgruppe: {demo.get('primary_target', 'unbekannt')}")
        
        # INE Demographics
        ine = analysis_data.get('ine_demographics', {})
        if ine.get('municipality_code'):
            ine_demo = ine.get('demographics', {})
            ine_scores = ine.get('scores', {})
            print("\n" + "-" * 70)
            print(f"🇪🇸 OFFIZIELLE INE-DATEN (Spanien):")
            print(f"   Stadt: {ine.get('city', 'Unbekannt')}")
            print(f"   Bevölkerung gesamt: {ine_demo.get('total_population', 0):,}")
            print(f"   Zielgruppe (20-39J): {ine_demo.get('young_percentage', 0)}% ({ine_demo.get('population_young_20_39', 0):,} Personen)")
            print(f"   Einkommensindex: {ine_demo.get('income_index', 100)} (100 = Durchschnitt Spanien)")
            print(f"\n   INE-Scores:")
            print(f"      Zielgruppen-Score:       {ine_scores.get('target_group_score', 0)}/100")
            print(f"      Kaufkraft-Score:         {ine_scores.get('purchasing_power_score', 0)}/100")
            print(f"      Marktgrößen-Score:       {ine_scores.get('market_size_score', 0)}/100")
            print(f"      Gesamtdemografie-Score:  {ine_scores.get('overall_demographic_score', 0)}/100")
        
        # NEW: Postal Code Data
        postal = analysis_data.get('postal_code_data', {})
        if postal and postal.get('demographics'):
            print("\n" + "-" * 70)
            print(f"📮 PLZ-SPEZIFISCHE DATEN:")
            print(f"   Postleitzahl: {postal.get('postal_code', 'N/A')}")
            print(f"   Provinz: {postal.get('province', 'Unknown')}")
            print(f"   Lage: {'ZENTRAL (High-Traffic)' if postal.get('is_central') else 'Peripher'}")
            print(f"   Urbane Klassifikation: {'Großstadt' if postal.get('is_urban') else 'Provinz'}")
            
            p_demo = postal.get('demographics', {})
            print(f"\n   Geschätzte Bevölkerung: {p_demo.get('estimated_population', 0):,}")
            print(f"   Zielgruppe (20-39J): {p_demo.get('young_percentage', 0)}%")
            print(f"   Einkommensindex: {p_demo.get('income_index', 100)}")
            
            if postal.get('notes'):
                print(f"\n   ℹ️  {postal.get('notes')}")
        
        # Accessibility
        access = analysis_data.get('accessibility', {})
        print("\n" + "-" * 70)
        print(f"🚗 ERREICHBARKEIT (ÖPNV/Parken):")
        print(f"   ÖPNV-Haltestellen: {access.get('public_transport_count', 0)}")
        print(f"   Parkplätze:        {access.get('parking_count', 0)}")
        if access.get('transport_types'):
            print(f"   Nahverkehr: {', '.join(access['transport_types'])}")
        
        # Fotocasa Rental Data
        rental = analysis_data.get('rental_market', {})
        if rental and rental.get('available'):
            print("\n" + "-" * 70)
            print(f"🏠 MIETMARKT-ANALYSE (Fotocasa):")
            print(f"   Objekte gefunden: {rental.get('properties_found', 0)}")
            print(f"   Durchschnittspreis: {rental.get('average_price_per_m2', 0)}€/m²")
            print(f"   {rental.get('market_rating', 'N/A')}")
            print(f"\n   Geschätzte Monatsmiete (350m²): {rental.get('monthly_estimate_350m2', 0):,}€")
            
            if rental.get('suitable_properties'):
                print(f"\n   Passende Objekte:")
                for prop in rental['suitable_properties'][:3]:
                    print(f"      • {prop['size']}m² - {prop['price_per_m2']}€/m² = {prop['price']:,.0f}€/Monat")
            
            if rental.get('note'):
                print(f"\n   ℹ️  {rental.get('note')}")
        
        # Risks & Opportunities
        print("\n" + "-" * 70)
        if score_data.get('risk_factors'):
            print("⚠️  RISIKEN:")
            for risk in score_data['risk_factors']:
                print(f"   • {risk}")
        
        if score_data.get('opportunities'):
            print("\n✨ CHANCEN:")
            for opp in score_data['opportunities']:
                print(f"   • {opp}")
        
        print("\n" + "=" * 70)

    def save_json_report(self, address: str, analysis_data: Dict, score_data: Dict):
        """Save report as JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_address = address.replace(' ', '_').replace(',', '')[:30]
        filename = f"{OUTPUT_DIR}/analysis_{safe_address}_{timestamp}.json"
        
        report = {
            'address': address,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_data,
            'score': score_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report gespeichert: {filename}")
        return filename
