# SmartGym Standort-Analyzer

KI-gestützte Standortanalyse für neue SmartGym-Studios in Spanien.

## Features

- 🔍 **Konkurrenz-Analyse**: Findet alle Fitness-Studios im Umkreis
- 👥 **Zielgruppen-Analyse**: Bewertet Wohngebiete, Büros, Studenten
- 🚗 **Erreichbarkeit**: ÖPNV, Parkplätze, Fahrzeiten
- 📊 **Gesamtbewertung**: Score 0-100 mit detailliertem Report

## Installation

```bash
cd ~/workspace/gym-locator
pip install requests
```

## Nutzung

```bash
# Mit API-Key als Umgebungsvariable
export GOOGLE_PLACES_API_KEY="dein-key"

# Analyse starten
python analyzer.py "Calle Mayor 1, Madrid"

# Oder interaktiv
python analyzer.py
```

## API-Zugänge

| API | Status | Beschreibung |
|-----|--------|--------------|
| Google Places API | ✅ Bereit | Konkurrenz, Demografie |
| Google Distance Matrix | ✅ Bereit | Erreichbarkeit |
| idealista API | 🔄 Pending | Mietpreise, Verfügbarkeit |
| INE (Spanien) | 🔄 Pending | Offizielle Demografie |

## Output

- **Console**: Farbige Übersicht mit Score
- **JSON**: Detaillierter Report in `reports/analysis_*.json`

## Bewertungskriterien

| Kategorie | Gewichtung |
|-----------|-----------|
| Konkurrenz-Dichte | 30% |
| Zielgruppen-Score | 25% |
| Erreichbarkeit | 25% |
| Markt-Sättigung | 20% |

**Rating:**
- 🟢 **Excellent** (75-100): Hoch empfohlen
- 🟡 **Moderate** (50-74): Möglich mit Einschränkungen
- 🔴 **Risky** (0-49): Nicht empfohlen