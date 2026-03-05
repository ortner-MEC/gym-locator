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
        print(f"   🏆 Konkurrenz:        {scores.get('competition', 0)}/100")
        print(f"   🚗 Erreichbarkeit:    {scores.get('accessibility', 0)}/100")
        print(f"   👥 Reichweite:        {scores.get('reachability', 0)}/100")
        print(f"   🏠 Mietkosten:        {scores.get('rental', 0)}/100")
        
        # Competition Details with intelligent filtering
        comp = analysis_data.get('competition', {})
        print("\n" + "-" * 70)
        print(f"🏢 KONKURRENZANALYSE (SmartGym-relevant):")
        
        if comp.get('filtering_explanation'):
            print(f"   📊 {comp['filtering_explanation'][0]}")
        
        print(f"   Gefunden: {comp.get('total_found', 0)} | Echte Gyms: {comp.get('real_count', 0)}")
        print(f"   Ø Bewertung: {comp.get('average_rating', 0)}/5.0 | Gute (≥4★): {comp.get('good_gyms_count', 0)}")
        print(f"   Marktsättigung: {comp.get('saturation', 'unbekannt').upper()}")
        
        if comp.get('population_estimate'):
            print(f"\n   👥 Markt:")
            print(f"      Einwohner: {comp['population_estimate']:,}")
            print(f"      Einwohner/Gym: {comp.get('people_per_gym', 'N/A')}")
            print(f"      Marktpotenzial: {comp.get('market_potential', 0)}/100")
        
        if comp.get('real_competitors'):
            print(f"\n   🏋️ Konkurrenz:")
            for gym in comp['real_competitors'][:5]:
                name = gym.get('name', 'Unbekannt')[:40]
                rating = gym.get('rating', '-')
                dist = gym.get('distance_km', '?')
                print(f"      • {name} ({rating}★, {dist}km)")
        
        if comp.get('closest_competitor'):
            c = comp['closest_competitor']
            print(f"\n   🔴 Nächster: {c['name']} ({c['distance_km']}km)")
        
        if comp.get('not_competition'):
            print(f"\n   ❌ Ausgeschlossen: {len(comp['not_competition'])} (Yoga, Boxen, etc.)")
        
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
    
    def save_detailed_report_prompt(self, address: str, prompt: str) -> str:
        """Save detailed franchise report prompt to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_address = address.replace(' ', '_').replace(',', '')[:30]
        filename = f"{OUTPUT_DIR}/detailed_report_{safe_address}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"   Detaillierter Report-Prompt gespeichert: {filename}")
        return filename
    
    def save_ki_prompt(self, address: str, prompt: str) -> str:
        """Save AI evaluation prompt to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_address = address.replace(' ', '_').replace(',', '')[:30]
        filename = f"{OUTPUT_DIR}/ki_prompt_{safe_address}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return filename
        
    def save_verification_checklist(self, address: str, analysis_data: Dict) -> str:
        """Save a markdown file with quick links for manual verification."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_address = address.replace(' ', '_').replace(',', '')[:30]
        filename = f"{OUTPUT_DIR}/verification_{safe_address}_{timestamp}.md"
        
        city = address.split(',')[0].strip()
        coords = analysis_data.get('coordinates', {})
        lat, lng = coords.get('lat'), coords.get('lng')
        
        md_content = f"# Manuelle Überprüfung: {address}\n\n"
        
        if lat and lng:
            md_content += f"## 📍 Standort\n"
            md_content += f"- [Google Maps (Standort)](https://www.google.com/maps/search/?api=1&query={lat},{lng})\n\n"
        
        md_content += f"## 🏙️ Stadt-Recherche\n"
        md_content += f"- [Wikipedia (DE)](https://de.wikipedia.org/w/index.php?search={city.replace(' ', '+')})\n"
        md_content += f"- [Wikipedia (ES)](https://es.wikipedia.org/w/index.php?search={city.replace(' ', '+')})\n"
        md_content += f"- [Fotocasa (Gewerbeimmobilien)](https://www.fotocasa.es/es/alquiler/locales/{city.replace(' ', '-').lower()}/todas-las-zonas/l)\n"
        md_content += f"- [Idealista (Gewerbeimmobilien)](https://www.idealista.com/alquiler-locales/{city.replace(' ', '-').lower()}/)\n\n"
        
        comp = analysis_data.get('competition', {})
        real_gyms = comp.get('real_competitors', [])
        possible_gyms = comp.get('possible_competitors', [])
        
        md_content += f"## 🏋️ Konkurrenz (Echte Gyms)\n"
        if not real_gyms:
            md_content += "Keine echten Gyms gefunden.\n\n"
        else:
            for gym in real_gyms:
                name = gym.get('name', 'Unbekannt')
                dist = gym.get('distance_km', '?')
                rating = gym.get('rating', '-')
                reviews = gym.get('review_count', 0)
                website = gym.get('analysis', {}).get('website') or gym.get('website', '')
                
                md_content += f"### {name}\n"
                md_content += f"- **Distanz:** {dist} km | **Bewertung:** {rating}★ ({reviews})\n"
                maps_query = f"{name} {city}".replace(' ', '+')
                md_content += f"- [Google Maps Link](https://www.google.com/maps/search/?api=1&query={maps_query})\n"
                if website:
                    md_content += f"- [Website]({website})\n"
                md_content += "\n"
        
        md_content += f"## 🤔 Mögliche Konkurrenz (Nische/CrossFit/Yoga)\n"
        if not possible_gyms:
            md_content += "Keine möglichen Konkurrenten gefunden.\n"
        else:
            for gym in possible_gyms[:5]:
                name = gym.get('name', 'Unbekannt')
                cat = gym.get('category', 'unknown')
                website = gym.get('analysis', {}).get('website') or gym.get('website', '')
                
                md_content += f"### {name} ({cat})\n"
                maps_query = f"{name} {city}".replace(' ', '+')
                md_content += f"- [Google Maps Link](https://www.google.com/maps/search/?api=1&query={maps_query})\n"
                if website:
                    md_content += f"- [Website]({website})\n"
                md_content += "\n"
                
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"   ✅ Verifizierungs-Checkliste erstellt: {filename}")
        return filename
