# SmartGym Standort-Analyzer

KI-gestützte Standortanalyse für neue SmartGym-Studios in Spanien.

## Features

### 🗺️ Geografische Analyse
- 🔍 **Konkurrenz-Analyse** – Alle Gyms im 2km-Radius finden + Bewertungen prüfen
- 👥 **Zielgruppen-Scan** – Wohngebiete, Büros, Unis in der Nähe zählen
- 🚗 **Erreichbarkeit** – ÖPNV, Parkplätze, Fahrzeiten

### ⏱️ Fahrzeit-Isochronen (NEU!)
- Berechnet Reichweite in 5/10/15 Minuten zu Fuß und mit dem Auto
- Schätzt potenzielle Kundschaft: *"15.240 Menschen erreichen das Studio in 10 Minuten zu Fuß"*
- Visualisiert Abdeckungsgrad als Prozentsatz

### 🇪🇸 Offizielle Demografie-Daten (INE)
- **Stadt-Level**: Bevölkerung, Altersstruktur (20-39 Zielgruppe), Einkommensindex
- **PLZ-Level**: Postleitzahl-genaue Hochrechnungen
- Zentrums vs. Peripherie-Einschätzung

### 📊 Bewertungssystem
- Gesamt-Score 0-100 mit 🟢🟡🔴 Rating
- Risiken & Chancen identifizieren
- Detaillierter JSON-Report

## Installation

```bash
cd ~/workspace/gym-locator

# Keine externen Dependencies nötig – nutzt nur Python Standardlib!
# (urllib für HTTP Requests)
```

## Nutzung

```bash
# Mit API-Key als Umgebungsvariable
export GOOGLE_PLACES_API_KEY="dein-key"

# Analyse starten (mit PLZ für genauere Daten)
python3 analyzer.py "Calle Mayor 1, 28013 Madrid"

# Oder nur Stadt
python3 analyzer.py "Plaza España, Barcelona"

# Oder interaktiv
python3 analyzer.py
```

## API-Zugänge

| API | Status | Beschreibung |
|-----|--------|--------------|
| Google Places API | ✅ Bereit | Konkurrenz, Demografie |
| Google Distance Matrix | ✅ Bereit | Fahrzeit-Isochronen |
| INE España (Stadt) | ✅ Bereit | Offizielle Demografie |
| INE España (PLZ) | ✅ Bereit | Postleitzahl-genaue Daten |
| idealista API | 🔄 Pending | Mietpreise, Verfügbarkeit |

## Output Beispiel

```
📊 GESAMTBEWERTUNG: 🟢 EXCELLENT
   Score: 82.5/100 Punkte

⏱️  FAHRZEIT-ISOCHRONEN:
   ZU FUSS erreichbar:
      5 Minuten:  24 Zonen
      10 Minuten: 89 Zonen
      ↳ Geschätzte Bevölkerung (10min): 17,355

📮 PLZ-SPEZIFISCHE DATEN:
   Postleitzahl: 28013
   Lage: ZENTRAL (High-Traffic)
   Geschätzte Bevölkerung: 12,450
   Zielgruppe (20-39J): 28.5%
```

## Bewertungskriterien

| Kategorie | Gewichtung |
|-----------|-----------|
| Konkurrenz-Dichte | 25% |
| Zielgruppen-Score (Google) | 20% |
| Erreichbarkeit (ÖPNV) | 20% |
| Reichweite (Fahrzeit) | 20% |
| Markt-Sättigung | 15% |
| + INE-Daten Bonus | +20% max |

**Rating:**
- 🟢 **Excellent** (75-100): Hoch empfohlen
- 🟡 **Moderate** (50-74): Möglich mit Einschränkungen
- 🔴 **Risky** (0-49): Nicht empfohlen

## Dateistruktur

```
gym-locator/
├── analyzer.py              # Haupt-CLI
├── config.py                # API-Keys & Einstellungen
├── modules/
│   ├── places_api.py        # Google Places Integration
│   ├── ine_api.py           # INE Stadt-Daten
│   ├── ine_postal.py        # INE Postleitzahl-Daten
│   ├── travel_time.py       # Fahrzeit-Isochronen
│   ├── scoring.py           # Bewertungsalgorithmus
│   └── report.py            # Report-Generierung
├── reports/                 # Generierte Analysen
└── README.md
```

## GitHub

**Repo:** [ortner-MEC/gym-locator](https://github.com/ortner-MEC/gym-locator)

## Roadmap

- [x] Fahrzeit-Isochronen
- [x] INE PLZ-Daten
- [ ] idealista Mietpreis-Analyse
- [ ] Heatmap-Visualisierung
- [ ] Mehrere Adressen vergleichen
- [ ] Benchmark-Datenbank (erfolgreiche Studios)