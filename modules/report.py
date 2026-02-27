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
        
        # Competition Details
        comp = analysis_data.get('competition', {})
        print("\n" + "-" * 70)
        print(f"🏢 KONKURRENZANALYSE:")
        print(f"   Anzahl Fitness-Studios im Umkreis: {comp.get('count', 0)}")
        print(f"   Durchschnittsbewertung: {comp.get('average_rating', 0)}/5.0")
        print(f"   Gut bewertete Gyms (≥4★): {comp.get('highly_rated_count', 0)}")
        
        if comp.get('competitors'):
            print("\n   Konkurrenten:")
            for gym in comp['competitors'][:5]:  # Show top 5
                name = gym.get('displayName', {}).get('text', 'Unbekannt')
                rating = gym.get('rating', '-')
                print(f"      • {name} ({rating}★)")
        
        # Demographics
        demo = analysis_data.get('demographics', {})
        print("\n" + "-" * 70)
        print(f"👥 ZIELGRUPPEN-ANALYSE:")
        print(f"   Wohngebiete:     {demo.get('residential_count', 0)}")
        print(f"   Bürogebäude:     {demo.get('office_count', 0)}")
        print(f"   Bildungseinrichtungen: {demo.get('young_count', 0)}")
        print(f"   Primäre Zielgruppe: {demo.get('primary_target', 'unbekannt')}")
        
        # Accessibility
        access = analysis_data.get('accessibility', {})
        print("\n" + "-" * 70)
        print(f"🚗 ERREICHBARKEIT:")
        print(f"   ÖPNV-Haltestellen: {access.get('public_transport_count', 0)}")
        print(f"   Parkplätze:        {access.get('parking_count', 0)}")
        if access.get('transport_types'):
            print(f"   Nahverkehr: {', '.join(access['transport_types'])}")
        
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