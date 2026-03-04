#!/usr/bin/env python3
"""SmartGym Location Analyzer - Main CLI Tool with Travel Time & Postal Code data."""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.places_api import PlacesAPI
from modules.ine_api import INEAPI
from modules.ine_postal import INEPostalCodeAPI
from modules.travel_time import TravelTimeAnalyzer
from modules.fotocasa_api import FotocasaAPI
from modules.scoring import LocationScorer
from modules.report import ReportGenerator
from config import DEFAULT_RADIUS_METERS, GOOGLE_PLACES_API_KEY

def check_api_key():
    """Verify API key is configured."""
    if not GOOGLE_PLACES_API_KEY:
        print("❌ Fehler: GOOGLE_PLACES_API_KEY nicht gefunden!")
        print("   Setze die Umgebungsvariable:")
        print("   export GOOGLE_PLACES_API_KEY='dein-key'")
        sys.exit(1)

def extract_city_from_address(address: str) -> str:
    """Extract city name from address string."""
    parts = address.split(',')
    if len(parts) >= 2:
        return parts[-1].strip()
    return address.split()[-1]

def extract_postal_code(address: str) -> str:
    """Extract 5-digit Spanish postal code from address."""
    match = re.search(r'\b(\d{5})\b', address)
    return match.group(1) if match else None

def analyze_location(address: str, radius: int = DEFAULT_RADIUS_METERS):
    """Main analysis workflow."""
    print(f"🔍 Analysiere: {address}")
    print(f"   Radius: {radius}m")
    
    # Initialize APIs
    places = PlacesAPI()
    ine = INEAPI()
    ine_postal = INEPostalCodeAPI()
    travel = TravelTimeAnalyzer()
    
    # Geocode address
    print("\n📍 Geocoding Adresse...")
    coords = places.geocode_address(address)
    if not coords:
        print("❌ Adresse konnte nicht gefunden werden!")
        return
    
    lat, lng = coords
    print(f"   Koordinaten: {lat:.4f}, {lng:.4f}")
    
    # Extract location identifiers
    city = extract_city_from_address(address)
    postal_code = extract_postal_code(address)
    
    if postal_code:
        print(f"   Postleitzahl erkannt: {postal_code}")
    
    # Estimate population from walking reachability
    # 2km radius, average suburban density ~2000 people/km² in Spain
    estimated_population = 25000  # Default
    
    # Run Google Places analyses with population estimate
    print("\n🏢 Analysiere Konkurrenz...")
    competition = places.analyze_competition(lat, lng, radius, population=estimated_population)
    print(f"   {competition['count']} Gyms gefunden")
    
    print("\n👥 Analysiere Zielgruppen (Google Places)...")
    demographics = places.analyze_target_demographics(lat, lng, radius)
    print(f"   {demographics['residential_count']} Wohngebiete")
    print(f"   {demographics['office_count']} Büros")
    
    print("\n🚗 Analysiere Erreichbarkeit (ÖPNV/Parken)...")
    accessibility = places.analyze_accessibility(lat, lng, radius)
    print(f"   {accessibility['public_transport_count']} ÖPNV-Haltestellen")
    print(f"   {accessibility['parking_count']} Parkplätze")
    
    # NEW: Travel time isochrone analysis
    print("\n⏱️  Berechne Fahrzeit-Isochronen...")
    travel_analysis = travel.analyze_isochrones(lat, lng)
    
    walking = travel_analysis['walking']
    print(f"   Zu Fuß erreichbar:")
    print(f"      5min: {walking['5min_reach']} Zonen")
    print(f"      10min: {walking['10min_reach']} Zonen")
    print(f"      Geschätzte Bevölkerung (10min): {walking['estimated_population_10min']:,}")
    
    driving = travel_analysis['driving']
    print(f"   Mit Auto erreichbar:")
    print(f"      10min: {driving['10min_reach']} Zonen")
    print(f"      Geschätzte Bevölkerung (10min): {driving['estimated_population_10min']:,}")
    
    # Run INE demographic analysis
    print(f"\n🇪🇸 Abfrage INE-Daten für: {city}...")
    ine_data = ine.analyze_location(city)
    
    if ine_data['municipality_code']:
        demo = ine_data['demographics']
        print(f"   Bevölkerung: {demo.get('total_population', 0):,}")
        print(f"   Zielgruppe (20-39): {demo.get('young_percentage', 0)}%")
        print(f"   Einkommensindex: {demo.get('income_index', 100)}")
    else:
        print("   ⚠️ Keine INE-Stadtdaten verfügbar")
    
    # NEW: Postal code specific analysis
    postal_data = None
    if postal_code:
        print(f"\n📮 PLZ-spezifische Analyse: {postal_code}...")
        postal_data = ine_postal.get_postal_code_data(postal_code, city)
        
        if postal_data.get('demographics'):
            p_demo = postal_data['demographics']
            print(f"   Geschätzte Bevölkerung: {p_demo.get('estimated_population', 0):,}")
            print(f"   Zielgruppe (20-39): {p_demo.get('young_percentage', 0)}%")
            print(f"   PLZ ist {'Zentrum' if postal_data.get('is_central') else 'Peripherie'}")
    
    # NEW: Web search for demographic data as fallback/enhancement
    web_demographics = {}
    print(f"\n🌐 Suche Demografie-Daten im Web...")
    try:
        from web_search import web_search
        city_clean = city.replace(' ', '+')
        search_query = f"{city} Murcia demografia poblacion renta ine 2024"
        web_results = web_search(search_query, count=5)
        
        if web_results and 'results' in web_results:
            # Extract relevant info from snippets
            web_info = []
            for result in web_results['results'][:3]:
                snippet = result.get('description', '')
                if snippet:
                    web_info.append(snippet[:200])
            
            web_demographics = {
                'source': 'web_search',
                'snippets': web_info,
                'query': search_query
            }
            print(f"   ✅ Web-Daten gefunden ({len(web_info)} Ergebnisse)")
        else:
            print("   ⚠️ Keine Web-Daten verfügbar")
    except Exception as e:
        print(f"   ⚠️ Web-Suche fehlgeschlagen: {e}")
    
    # NEW: Fotocasa rental market analysis
    print("\n🏠 Analysiere Mietmarkt (Fotocasa)...")
    fotocasa = FotocasaAPI()
    rental_data = fotocasa.analyze_rental_market(lat, lng)
    
    if rental_data['available']:
        print(f"   Objekte gefunden: {rental_data['properties_found']}")
        print(f"   Durchschnitt: {rental_data['average_price_per_m2']}€/m²")
        print(f"   Schätzung 350m²: {rental_data['monthly_estimate_350m2']}€/Monat")
        print(f"   Bewertung: {rental_data['market_rating']}")
    else:
        print("   Keine Daten verfügbar")
    
    # Compile data
    analysis_data = {
        'competition': competition,
        'demographics': demographics,
        'accessibility': accessibility,
        'travel_analysis': travel_analysis,
        'ine_demographics': ine_data,
        'postal_code_data': postal_data,
        'rental_market': rental_data,
        'web_demographics': web_demographics,
        'coordinates': {'lat': lat, 'lng': lng}
    }
    
    # Calculate enhanced score
    print("\n📊 Berechne Gesamtbewertung...")
    score_data = LocationScorer.calculate_overall_score(analysis_data)
    
    # Generate report
    reporter = ReportGenerator()
    reporter.generate_console_report(address, analysis_data, score_data)
    reporter.save_json_report(address, analysis_data, score_data)
    
    # Generate AI evaluation prompt
    print("\n🤖 Bereite KI-Gutachten vor...")
    ki_prompt = generate_ki_evaluation_prompt(address, analysis_data, score_data)
    ki_prompt_path = reporter.save_ki_prompt(address, ki_prompt)
    print(f"   KI-Prompt gespeichert: {ki_prompt_path}")
    
    return score_data, ki_prompt

def generate_ki_evaluation_prompt(address: str, data: Dict, score: Dict) -> str:
    """Generate a comprehensive prompt for AI evaluation."""
    comp = data.get('competition', {})
    travel = data.get('travel_analysis', {})
    rental = data.get('rental_market', {})
    web_demo = data.get('web_demographics', {})
    ine_data = data.get('ine_demographics', {})
    
    # Format competition list
    real_gyms = comp.get('real_competitors', [])
    gym_list = "\n".join([
        f"  - {g['name']} ({g.get('rating', '-')}★, {g.get('distance_km', '?')}km, {g.get('category', 'unknown')})"
        for g in real_gyms[:5]
    ])
    
    walking = travel.get('walking', {})
    driving = travel.get('driving', {})
    
    prompt = f"""DU BIST EIN EXPERTE FÜR FITNESS-STUDIO-STANDORTE IN SPANIEN. Gib ein professionelles Gutachten ab.

=== DEMOGRAFIE-DATEN ===
INE-Daten: {'Verfügbar' if ine_data.get('municipality_code') else 'Nicht verfügbar'}
Web-Recherche: {'Verfügbar' if web_demo.get('snippets') else 'Nicht verfügbar'}
{chr(10).join(['- ' + s[:100] + '...' for s in web_demo.get('snippets', [])[:3]]) if web_demo.get('snippets') else ''}

=== STANDORT ===
Adresse: {address}
Koordinaten: {data.get('coordinates', {}).get('lat')}, {data.get('coordinates', {}).get('lng')}

=== KONKURRENZANALYSE ===
Gefundene Gyms: {comp.get('total_found', 0)}
Echte Konkurrenten: {comp.get('real_count', 0)}
Details:{gym_list if gym_list else '  (keine relevante Konkurrenz)'}

Nächster Konkurrent: {comp.get('closest_competitor', {}).get('name', 'N/A')} ({comp.get('closest_competitor', {}).get('distance_km', '?')}km)

Markt-Metriken:
- Einwohner pro Gym: {comp.get('people_per_gym', 'N/A')}
- Marktpotenzial: {comp.get('market_potential', 'N/A')}/100
- Marktsättigung: {comp.get('saturation', 'unknown')}

=== REICHWEITE (FAHRZEIT-ISOCHRONEN) ===
Zu Fuß (10min): {walking.get('estimated_population_10min', 0):,} Menschen ({walking.get('10min_reach', 0)} Zonen)
Mit Auto (10min): {driving.get('estimated_population_10min', 0):,} Menschen ({driving.get('10min_reach', 0)} Zonen)

=== MIETMARKT ===
Durchschnitt: {rental.get('average_price_per_m2', 'N/A')}€/m²
Schätzung 350m²: {rental.get('monthly_estimate_350m2', 'N/A')}€/Monat
Bewertung: {rental.get('market_rating', 'N/A')}

=== ALGORITHMUS-SCORING ===
Gesamtpunktzahl: {score.get('total_score', 'N/A')}/100
Einzelscores:
- Konkurrenz: {score.get('individual_scores', {}).get('competition', 'N/A')}/100
- Erreichbarkeit: {score.get('individual_scores', {}).get('accessibility', 'N/A')}/100
- Reichweite: {score.get('individual_scores', {}).get('reachability', 'N/A')}/100
- Mietkosten: {score.get('individual_scores', {}).get('rental', 'N/A')}/100

=== DEINE AUFGABE ===
Gib eine PROFESSIONELLE BEWERTUNG (Skala 0-100) mit Begründung:

1. **Gesamtbewertung (0-100):** Eine konkrete Zahl basierend auf allen Faktoren
   - 90-100: Herausragend, sofortiger Go
   - 80-89: Sehr gut, klare Empfehlung  
   - 65-79: Gut, aber mit Risiken/Anpassungen
   - 50-64: Durchschnitt, nur mit Spezialstrategie
   - 0-49: Abgelehnt, zu viele rote Fahnen

2. **Begründung (3-4 Sätze):** Warum diese Zahl? Welche Faktoren wie gewichten?

3. **Haupt-Risiken (1-2 Punkte):** Was könnte schiefgehen?

4. **Haupt-Chancen (1-2 Punkte):** Wo liegt das Potenzial?

5. **Strategie-Empfehlung (1 Satz):** Konkrete Handlungsempfehlung

Antworte in DEUTSCH. Format:
**Bewertung: [Zahl]/100**
**Begründung:** [Text]
**Risiken:** [Text]
**Chancen:** [Text]  
**Strategie:** [Text]"""
    
    return prompt

def main():
    check_api_key()
    
    print("=" * 70)
    print("🏋️  SMARTGYM STANDORT-ANALYZER".center(70))
    print("   Google Places + INE España + Fahrzeit-Isochronen".center(70))
    print("=" * 70)
    
    # Get input
    if len(sys.argv) > 1:
        address = ' '.join(sys.argv[1:])
    else:
        address = input("\n📍 Adresse eingeben (z.B. 'Calle Mayor 1, 28013 Madrid'): ").strip()
    
    if not address:
        print("❌ Keine Adresse eingegeben!")
        sys.exit(1)
    
    # Run analysis
    try:
        result, ki_prompt = analyze_location(address)
        if result:
            print(f"\n✅ Analyse abgeschlossen!")
            print(f"   Gesamtpunktzahl: {result['total_score']}/100")
            print(f"\n🤖 KI-Gutachten kann jetzt erstellt werden.")
            return result, ki_prompt
    except KeyboardInterrupt:
        print("\n\n⚠️ Analyse abgebrochen.")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    return None, None

if __name__ == '__main__':
    main()
