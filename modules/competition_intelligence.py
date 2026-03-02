"""Smart competition intelligence using Google Place Details + Review + Website analysis."""
import math
import json
import urllib.request
import urllib.error
import re
from typing import Dict, List, Optional
from config import GOOGLE_PLACES_API_KEY


class CompetitionIntelligence:
    """
    Categorizes fitness places by analyzing their Google Reviews and details.
    
    Instead of guessing from the name alone, we look at what customers actually
    say about each place to determine if it's a real full-service gym.
    """
    
    # Keywords in reviews that indicate a REAL full-service gym
    GYM_REVIEW_KEYWORDS = [
        # Equipment (ES)
        'máquinas', 'maquinas', 'pesas', 'mancuernas', 'barra', 'banco',
        'cinta de correr', 'elíptica', 'eliptica', 'bicicleta estática',
        'poleas', 'smith', 'rack', 'press', 'sentadilla',
        # Equipment (EN)
        'weights', 'dumbbells', 'barbell', 'treadmill', 'machines',
        'bench press', 'squat rack', 'cable', 'elliptical',
        # Gym-specific terms (ES)
        'gimnasio', 'sala de musculación', 'musculacion', 'zona de cardio',
        'zona de pesas', 'aparatos',
        # Gym-specific terms (EN)  
        'gym', 'workout', 'weight room', 'cardio area', 'free weights',
        # Membership / access
        '24h', '24 horas', 'cuota', 'mensual', 'abono',
        'membership', 'monthly',
    ]
    
    # Keywords that indicate it's NOT a traditional gym (niche/other)
    NOT_GYM_KEYWORDS = [
        # Yoga/Pilates/Mind-body
        'yoga', 'pilates', 'meditación', 'meditation', 'chakra', 'asana',
        'mindfulness', 'stretching class',
        # Combat sports only (studios that ONLY do combat)
        'boxeo', 'boxing ring', 'kickboxing', 'muay thai', 'mma',
        'jiu jitsu', 'judo', 'karate', 'taekwondo', 'artes marciales',
        # Dance
        'danza', 'baile', 'dance', 'salsa', 'bachata', 'ballet',
        # Swimming / water
        'piscina', 'natación', 'natacion', 'swimming',
        # Municipal / public sports facilities (halls, stadiums)
        'pabellón', 'pabellon', 'polideportivo', 'municipal',
        'ayuntamiento', 'skatepark', 'skate', 'campo de fútbol',
        'pista de atletismo', 'campo de tiro', 'tiro',
        # Physiotherapy / medical
        'fisioterapia', 'rehabilitación', 'rehabilitacion', 'physio',
        'masaje', 'massage', 'quiropráctico',
        # Pure personal training (tiny studios, 1-2 trainers)
        'entrenamiento personal exclusivo', 'solo con cita',
        # CrossFit boxes (different business model, different target)
        'crossfit', 'wod', 'box de crossfit',
    ]
    
    # Keywords that strongly indicate full-service gym even if name is ambiguous
    STRONG_GYM_INDICATORS = [
        'gimnasio completo', 'sala de fitness', 'zona de musculación',
        'free weights', 'weight training', 'strength training',
        'bodybuilding', 'culturismo', 'powerlifting',
        'open gym', 'self-service', 'autoservicio',
        'arena', 'fitnesspark', 'fitness park',
    ]
    
    # Name patterns that are NEVER real gyms
    NAME_BLACKLIST = [
        'pabellón', 'pabellon', 'polideportivo', 'skatepark',
        'piscina', 'swimming pool', 'aqualia',
        'campo de', 'club de tiro', 'circuito',
        'centro deportivo',  # Municipal sports center, not a gym
    ]
    
    # Name patterns that BOOST gym confidence (override unclear)
    NAME_WHITELIST = [
        'arena', 'fitnesspark', 'fitness park', 'mcfit', 'basic-fit',
        'viva gym', 'altafit', 'smart gym', 'smartgym',
    ]

    def __init__(self, origin_lat: float = None, origin_lng: float = None, 
                 api_key: str = GOOGLE_PLACES_API_KEY):
        self.origin_lat = origin_lat
        self.origin_lng = origin_lng
        self.api_key = api_key

    def _haversine(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Distance in meters between two coordinates."""
        R = 6371000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lng2 - lng1)
        a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # Website analysis keywords
    WEBSITE_GYM_KEYWORDS = [
        # Equipment
        'maquinas', 'máquinas', 'pesas', 'mancuernas', 'barra', 'banco', 'rack',
        'cinta', 'eliptica', 'elíptica', 'bicicleta', 'cardio', 'musculacion',
        'musculación', 'aparatos', 'polea', 'cable', 'press', 'sentadilla',
        'weights', 'dumbbells', 'treadmill', 'machines', 'bench', 'squat',
        # Access
        '24h', '24 horas', '24/7', 'acceso 24h', 'abierto 24', 'acceso libre',
        '24 hours', '24 hour access', 'open 24', 'self-service', 'autoservicio',
        # Membership
        'tarifa', 'mensual', 'abono', 'cuota', 'membresia', 'suscripcion',
        'monthly', 'membership', 'subscription', 'monthly fee',
        # Services
        'gimnasio', 'fitness', 'entrenamiento', 'workout', 'strength',
        'vestuario', 'duchas', 'taquillas', 'locker', 'changing room',
    ]
    
    WEBSITE_NOT_GYM_KEYWORDS = [
        # Classes that indicate non-24h or niche
        'clases dirigidas', 'actividades dirigidas', 'monitores', 'profesores',
        'spinning', 'pilates', 'yoga', 'zumba', 'body pump', 'aqua gym',
        'natación', 'piscina', 'piscinas', 'swimming',
        # Personal training focus
        'entrenamiento personal', 'personal trainer', 'solo con cita',
        'cita previa', 'appointment only', 'by appointment',
        # Other
        'fisioterapia', 'fisio', 'masaje', 'massage', 'spa', 'wellness',
        'crossfit', 'box de crossfit', 'crossfit box',
    ]
    
    def fetch_place_details(self, place_id: str) -> Dict:
        """Fetch reviews + editorial summary + website from Google Places API."""
        url = f'https://places.googleapis.com/v1/places/{place_id}'
        headers = {
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'id,displayName,editorialSummary,reviews,primaryType,primaryTypeDisplayName,websiteUri'
        }
        
        req = urllib.request.Request(url)
        for k, v in headers.items():
            req.add_header(k, v)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"   ⚠️ Details-Fehler für {place_id}: {e}")
            return {}
    
    def fetch_website_content(self, url: str, timeout: int = 10) -> str:
        """Fetch and extract text content from a website."""
        if not url or not url.startswith('http'):
            return ""
        
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                
                # Extract text (simple approach)
                # Remove scripts and styles
                html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
                
                # Extract text from common content areas
                text_parts = []
                
                # Look for main content areas
                for tag in ['main', 'article', 'section', 'div class="content"', 'div id="content"']:
                    matches = re.findall(rf'<{tag}[^>]*>(.*?)</{tag.split()[0]}>', html, re.DOTALL | re.IGNORECASE)
                    for match in matches[:2]:  # First 2 matches
                        text = re.sub(r'<[^>]+>', ' ', match)
                        text_parts.append(text)
                
                # If no content areas found, extract all text
                if not text_parts:
                    text = re.sub(r'<[^>]+>', ' ', html)
                    text_parts.append(text)
                
                # Clean and limit
                full_text = ' '.join(text_parts)
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                return full_text[:5000].lower()  # First 5000 chars
                
        except urllib.error.HTTPError as e:
            print(f"   ⚠️ Website HTTP {e.code}: {url[:50]}...")
            return ""
        except Exception as e:
            print(f"   ⚠️ Website-Fehler: {url[:50]}... ({str(e)[:50]})")
            return ""

    def analyze_content(self, details: Dict, website_text: str, place_name: str = '') -> Dict:
        """Analyze reviews + website + name to determine what kind of place this really is."""
        reviews = details.get('reviews', [])
        editorial = details.get('editorialSummary', {}).get('text', '')
        primary_type = details.get('primaryType', '')
        primary_type_name = details.get('primaryTypeDisplayName', {}).get('text', '')
        website = details.get('websiteUri', '')
        name_lower = place_name.lower()
        
        # Check name blacklist first (instant reject)
        for bl in self.NAME_BLACKLIST:
            if bl in name_lower:
                return {
                    'category': 'not_competition',
                    'confidence': 90,
                    'gym_score': 0, 'not_gym_score': 10, 'net_score': -10,
                    'gym_matches': [], 'not_gym_matches': [f'name:{bl}'],
                    'review_count': len(reviews),
                    'primary_type': primary_type,
                    'primary_type_name': primary_type_name,
                    'website': website, 'has_editorial': bool(editorial),
                    'has_website_data': bool(website_text),
                }
        
        # Combine all content: reviews + editorial + website
        all_text = editorial.lower() + ' '
        for review in reviews[:5]:
            text = review.get('text', {}).get('text', '')
            all_text += text.lower() + ' '
        
        # Add website content (if fetched successfully)
        has_website = bool(website_text)
        if has_website:
            all_text += website_text + ' '
        
        # Also check name for keywords
        name_and_text = name_lower + ' ' + all_text
        
        # === REVIEW-BASED SCORING ===
        review_gym_score = 0
        review_matches = []
        for kw in self.GYM_REVIEW_KEYWORDS:
            if kw in all_text:
                review_gym_score += 1
                review_matches.append(kw)
        
        # === WEBSITE-BASED SCORING (higher weight!) ===
        website_gym_score = 0
        website_matches = []
        if has_website:
            for kw in self.WEBSITE_GYM_KEYWORDS:
                if kw in website_text:
                    website_gym_score += 2  # Higher weight for website
                    website_matches.append(f"web:{kw}")
            
            # 24h access on website is STRONG signal
            if any(x in website_text for x in ['24h', '24 horas', '24/7', 'abierto 24']):
                website_gym_score += 5
                website_matches.append("⭐web:24h-access")
        
        # === COMBINED SCORING ===
        gym_score = review_gym_score + website_gym_score
        gym_matches = review_matches[:3] + website_matches[:3]
        
        # Strong indicators in name
        for kw in self.STRONG_GYM_INDICATORS:
            if kw in name_and_text:
                gym_score += 3
                gym_matches.append(f"⭐{kw}")
        
        # Name contains "gym" or "gimnasio"
        if any(w in name_lower for w in ['gym', 'gimnasio', 'fitness']):
            gym_score += 3
            gym_matches.append('⭐name:gym/gimnasio/fitness')
        
        # Name whitelist
        for wl in self.NAME_WHITELIST:
            if wl in name_lower:
                gym_score += 4
                gym_matches.append(f'⭐name:{wl}')
        
        # === NON-GYM SCORING ===
        not_gym_score = 0
        not_gym_matches = []
        for kw in self.NOT_GYM_KEYWORDS:
            if kw in name_and_text:
                not_gym_score += 1
                not_gym_matches.append(kw)
        
        # Website non-gym signals
        if has_website:
            for kw in self.WEBSITE_NOT_GYM_KEYWORDS:
                if kw in website_text:
                    not_gym_score += 2
                    not_gym_matches.append(f"web:{kw}")
        
        # Primary type bonus
        if primary_type in ('gym', 'fitness_center', 'health_club'):
            gym_score += 3
        elif primary_type in ('yoga_studio', 'swimming_pool', 'sports_complex', 'stadium'):
            not_gym_score += 3
        
        # === DETERMINE CATEGORY ===
        net_score = gym_score - not_gym_score
        
        # CrossFit special case
        is_crossfit = 'crossfit' in name_lower or 'crossfit' in all_text
        
        if is_crossfit:
            category = 'possible_competitor'
            confidence = 60
        elif net_score >= 5:
            category = 'direct_competitor'
            confidence = min(100, 60 + net_score * 8)
        elif net_score >= 2:
            category = 'possible_competitor'
            confidence = 50 + net_score * 10
        elif net_score <= -3:
            category = 'not_competition'
            confidence = min(100, 60 + abs(net_score) * 8)
        elif net_score <= -1:
            category = 'unclear'
            confidence = 40
        else:
            category = 'unclear'
            confidence = 30
        
        # Fallback if no data at all
        if not reviews and not editorial and not website_text:
            if gym_score > 0:
                category = 'possible_competitor'
                confidence = 20
            else:
                category = 'no_data'
                confidence = 10
        
        return {
            'category': category,
            'confidence': confidence,
            'gym_score': gym_score,
            'not_gym_score': not_gym_score,
            'net_score': net_score,
            'gym_matches': gym_matches[:5],
            'not_gym_matches': not_gym_matches[:3],
            'review_count': len(reviews),
            'has_website_data': has_website,
            'primary_type': primary_type,
            'primary_type_name': primary_type_name,
            'website': website,
            'has_editorial': bool(editorial),
        }

    def analyze_all(self, places: List[Dict], population: int = 20000) -> Dict:
        """Full analysis: fetch details, categorize, calculate market metrics."""
        analyzed = []
        
        print(f"   🔍 Analysiere {len(places)} Einträge im Detail...")
        
        for i, place in enumerate(places):
            name = place.get('displayName', {}).get('text', 'Unbekannt')
            place_id = place.get('id', '')
            rating = place.get('rating', 0)
            review_count = place.get('userRatingCount', 0)
            
            # Location & distance
            loc = place.get('location', {})
            plat, plng = loc.get('latitude'), loc.get('longitude')
            dist_m = None
            if plat and plng and self.origin_lat and self.origin_lng:
                dist_m = self._haversine(self.origin_lat, self.origin_lng, plat, plng)
            
            # Fetch details + reviews + website
            details = self.fetch_place_details(place_id) if place_id else {}
            
            # Fetch website content if URL available
            website_url = details.get('websiteUri', '')
            website_text = ""
            if website_url:
                website_text = self.fetch_website_content(website_url)
                if website_text:
                    print(f"      🌐 Website analysiert ({len(website_text)} Zeichen)")
            
            review_analysis = self.analyze_content(details, website_text, place_name=name)
            
            cat = review_analysis['category']
            conf = review_analysis['confidence']
            icon = {'direct_competitor': '🏋️', 'possible_competitor': '🤔', 
                    'not_competition': '❌', 'unclear': '❓', 'no_data': '📭'}.get(cat, '❓')
            
            web_icon = "🌐" if review_analysis.get('has_website_data') else ""
            print(f"   {icon} {web_icon} {name} → {cat} ({conf}% sicher)")
            if review_analysis['gym_matches']:
                print(f"      Gym-Signale: {', '.join(review_analysis['gym_matches'][:3])}")
            if review_analysis['not_gym_matches']:
                print(f"      Nicht-Gym: {', '.join(review_analysis['not_gym_matches'][:3])}")
            
            analyzed.append({
                'name': name,
                'rating': rating,
                'review_count': review_count,
                'distance_m': dist_m,
                'distance_km': round(dist_m / 1000, 2) if dist_m else None,
                'category': cat,
                'confidence': conf,
                'is_real_competition': cat == 'direct_competitor',
                'analysis': review_analysis,
            })
        
        # Sort: real competitors first, then by distance
        analyzed.sort(key=lambda x: (
            0 if x['category'] == 'direct_competitor' else
            1 if x['category'] == 'possible_competitor' else 2,
            x.get('distance_m') or 99999
        ))
        
        # Split into categories
        real = [p for p in analyzed if p['category'] == 'direct_competitor']
        possible = [p for p in analyzed if p['category'] == 'possible_competitor']
        not_comp = [p for p in analyzed if p['category'] in ('not_competition', 'unclear', 'no_data')]
        
        # Market metrics
        real_count = len(real)
        if real_count > 0:
            avg_rating = sum(p['rating'] for p in real if p['rating']) / max(1, len([p for p in real if p['rating']]))
            distances = [p['distance_m'] for p in real if p['distance_m']]
            closest = min(real, key=lambda x: x['distance_m'] or 99999) if real else None
        else:
            avg_rating = 0
            closest = None
        
        people_per_gym = population // real_count if real_count > 0 else 0
        
        if real_count == 0:
            market_potential = 95
            saturation = 'none'
        elif people_per_gym > 8000:
            market_potential = 85
            saturation = 'very_low'
        elif people_per_gym > 5000:
            market_potential = 70
            saturation = 'low'
        elif people_per_gym > 3000:
            market_potential = 50
            saturation = 'medium'
        elif people_per_gym > 2000:
            market_potential = 30
            saturation = 'high'
        else:
            market_potential = 15
            saturation = 'oversaturated'
        
        return {
            'total_found': len(places),
            'real_competitors': real,
            'real_count': real_count,
            'possible_competitors': possible,
            'not_competition': not_comp,
            'average_rating': round(avg_rating, 1),
            'good_gyms_count': len([p for p in real if p['rating'] and p['rating'] >= 4.0]),
            'closest_competitor': closest,
            'avg_distance_m': sum(p['distance_m'] for p in real if p['distance_m']) / max(1, len([p for p in real if p['distance_m']])) if real else None,
            'population_estimate': population,
            'people_per_gym': people_per_gym if real_count > 0 else 'N/A',
            'market_potential': market_potential,
            'saturation': saturation,
        }

    def generate_explanation(self, result: Dict) -> List[str]:
        """Human-readable summary."""
        lines = []
        total = result['total_found']
        real = result['real_count']
        poss = len(result.get('possible_competitors', []))
        excluded = len(result.get('not_competition', []))
        
        lines.append(f"Von {total} Einträgen: {real} echte Gyms, {poss} möglich, {excluded} ausgeschlossen")
        
        if result.get('closest_competitor'):
            c = result['closest_competitor']
            lines.append(f"Nächstes Gym: {c['name']} ({c['distance_km']}km)")
        
        return lines
