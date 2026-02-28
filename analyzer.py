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
    
    # Run Google Places analyses
    print("\n🏢 Analysiere Konkurrenz...")
    competition = places.analyze_competition(lat, lng, radius)
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
        'coordinates': {'lat': lat, 'lng': lng}
    }
    
    # Calculate enhanced score
    print("\n📊 Berechne Gesamtbewertung...")
    score_data = LocationScorer.calculate_overall_score(analysis_data)
    
    # Generate report
    reporter = ReportGenerator()
    reporter.generate_console_report(address, analysis_data, score_data)
    reporter.save_json_report(address, analysis_data, score_data)
    
    return score_data

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
        result = analyze_location(address)
        if result:
            print(f"\n✅ Analyse abgeschlossen!")
            print(f"   Gesamtpunktzahl: {result['total_score']}/100")
    except KeyboardInterrupt:
        print("\n\n⚠️ Analyse abgebrochen.")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
