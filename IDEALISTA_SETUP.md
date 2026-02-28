# Idealista API - Zugang beantragen

## Schritt-für-Schritt Anleitung

### 1. Account erstellen
1. Gehe zu: https://developers.idealista.com/
2. Klicke auf **"Sign up"** oder **"Create an account"**
3. Wähle: **"I'm a developer"**

### 2. API-Zugang beantragen
1. Logge dich ein
2. Klicke auf **"Request API access"**
3. Fülle das Formular aus:

**Projekt-Name:** SmartGym Location Analyzer

**Beschreibung (kopieren):**
```
Internal analytics tool for SmartGym franchise expansion in Spain. 
We analyze commercial rental prices and availability to evaluate 
potential gym locations. Non-commercial research use only.

Features:
- Query commercial premises (local/nave) rental prices
- Calculate price per m² for 350m² gym spaces
- Compare neighborhoods for franchise suitability
- Data visualization for internal decision making
```

**Use Case:** Internal business analysis / Location intelligence

**Expected API calls:** ~100/month during research phase

### 3. Warte auf Freigabe
- Dauer: 1-3 Werktage
- Du bekommst eine E-Mail mit **API Key** und **API Secret**

### 4. Konfiguration im Analyzer

Füge die Credentials hinzu:

```bash
# In ~/.zshrc oder ~/.bashrc:
export IDEALISTA_API_KEY="dein-api-key"
export IDEALISTA_API_SECRET="dein-api-secret"

# Oder temporär für diese Session:
export IDEALISTA_API_KEY="xxx"
export IDEALISTA_API_SECRET="yyy"
```

### 5. Test

```bash
cd ~/workspace/gym-locator
python3 -c "from modules.idealista_api import IdealistaAPI; i = IdealistaAPI(); print('API bereit!')"
```

## Was die idealista API liefert

| Datenpunkt | Nutzen für SmartGym |
|------------|---------------------|
| **Mietpreis pro m²** | Kostenkalkulation für 350m² |
| **Verfügbare Objekte** | Gibt es passende Gewerbeflächen? |
| **Nachfrage-Index** | Wie schnell werden Anzeigen geklickt? |
| **Preisentwicklung** | Steigen oder sinken die Mieten? |

## Beispiel-Output nach Integration

```
🏠 MIETMARKT-ANALYSE (Idealista):
   Objekte gefunden: 12
   Passend für 350m² Gym: 4
   
   Durchschnittspreis: 11.50 €/m² 🟡 Moderat
   Geschätzte Monatsmiete (350m²): 4,025 €
   
   Beste Optionen:
   • Calle Alcalá 45 - 3,850€/Monat (11€/m²)
   • Avenida América 12 - 4,200€/Monat (12€/m²)
```

## Troubleshooting

**Fehler: "Unauthorized"**
→ API Key nicht gesetzt oder noch nicht freigeschaltet

**Fehler: "Rate limit exceeded"**
→ Zu viele Requests. Max 100/Tag im Basic-Plan

**Keine Ergebnisse**
→ Idealista hat begrenzte Daten für Gewerbeflächen. 
→ Alternative: Fotocasa API oder Web-Scraping als Fallback

## Alternative: Fotocasa API

Falls idealista ablehnt:
1. https://www.fotocasa.es/es/api/doc
2. Ähnlicher Prozess, oft einfacherer Zugang

## Status

- [ ] Account erstellt
- [ ] API-Zugang beantragt
- [ ] Credentials erhalten
- [ ] Im Analyzer konfiguriert
- [ ] Erster Test erfolgreich