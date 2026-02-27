#!/usr/bin/env python3
"""SmartGym Location Analyzer - Main CLI Tool."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.places_api import PlacesAPI
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

def analyze_location(address: str, radius: int = DEFAULT_RADIUS_METERS):
    """Main analysis workflow."""
    print(f"🔍 Analysiere: {address}")
    print(f"   Radius: {radius}m")
    
    # Initialize APIs
    places = PlacesAPI()
    
    # Geocode address
    print("\n📍 Geocoding Adresse...")
    coords = places.geocode_address(address)
    if not coords:
        print("❌ Adresse konnte nicht gefunden werden!")
        return
    
    lat, lng = coords
    print(f"   Koordinaten: {lat:.4f}, {lng:.4f}")
    
    # Run analyses
    print("\n🏢 Analysiere Konkurrenz...")
    competition = places.analyze_competition(lat, lng, radius)
    print(f"   {competition['count']} Gyms gefunden")
    
    print("\n👥 Analysiere Zielgruppen...")
    demographics = places.analyze_target_demographics(lat, lng, radius)
    print(f"   {demographics['residential_count']} Wohngebiete")
    print(f"   {demographics['office_count']} Büros")
    
    print("\n🚗 Analysiere Erreichbarkeit...")
    accessibility = places.analyze_accessibility(lat, lng, radius)
    print(f"   {accessibility['public_transport_count']} ÖPNV-Haltestellen")
    
    # Compile data
    analysis_data = {
        'competition': competition,
        'demographics': demographics,
        'accessibility': accessibility,
        'coordinates': {'lat': lat, 'lng': lng}
    }
    
    # Calculate score
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
    print("   Powered by Google Places API".center(70))
    print("=" * 70)
    
    # Get input
    if len(sys.argv) > 1:
        address = ' '.join(sys.argv[1:])
    else:
        address = input("\n📍 Adresse eingeben (z.B. 'Calle Mayor 1, Madrid'): ").strip()
    
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