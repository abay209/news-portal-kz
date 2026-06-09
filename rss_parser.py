import feedparser
import requests
from bs4 import BeautifulSoup
import os
import uuid
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from app.models import News, Category, Source
from app import create_app, db

# Category keywords with scoring weights (Russian + Kazakh + English)
CATEGORY_KEYWORDS = {
    'cat_politics': [
        # Russian
        'парламент', 'депутат', 'президент', 'токаев', 'правительство', 'министр',
        'акимат', 'закон', 'политика', 'выборы', 'референдум', 'сенат', 'мажилис',
        'премьер', 'указ', 'постановление', 'партия', 'аким', 'антикор', 'конституция',
        # Kazakh
        'үкімет', 'президент', 'парламент', 'депутат', 'министр', 'заң', 'сайлау',
        'мәжіліс', 'сенат', 'саясат', 'акимат', 'аким', 'жарлық',
        # English
        'white house', 'president', 'senate', 'congress', 'parliament', 'government',
        'minister', 'election', 'policy', 'political', 'democrat', 'republican',
        'trump', 'biden', 'putin', 'xi jinping',
    ],
    'cat_sport': [
        # Russian
        'спорт', 'матч', 'футбол', 'хоккей', 'бокс', 'олимпиада', 'чемпионат',
        'гол', 'кубок', 'турнир', 'головкин', 'теннис', 'баскетбол', 'волейбол',
        'легкая атлетика', 'плавание', 'борьба', 'тяжелая атлетика', 'киберспорт',
        'клуб', 'стадион', 'тренер', 'сборная', 'лига', 'игрок', 'атлет', 'чемпион',
        # Kazakh
        'спорт', 'матч', 'футбол', 'хоккей', 'бокс', 'олимпиада', 'чемпионат',
        'кубок', 'турнир', 'теннис', 'баскетбол', 'жеңімпаз', 'ұтыс',
        # English
        'sport', 'football', 'soccer', 'basketball', 'hockey', 'tennis', 'boxing',
        'olympic', 'championship', 'tournament', 'league', 'match', 'game',
        'fifa', 'nba', 'nhl', 'uefa', 'formula 1', 'f1', 'athlete', 'coach',
        'transfer', 'stadium', 'score', 'goal',
    ],
    'cat_economy': [
        # Russian
        'тенге', 'финансы', 'банк', 'нефть', 'экономика', 'бизнес', 'налог',
        'курс валют', 'инвестиции', 'ввп', 'акции', 'криптовалюта', 'биржа',
        'инфляция', 'бюджет', 'кредит', 'ипотека', 'торговля', 'экспорт', 'импорт',
        'рынок', 'предприниматель', 'стартап', 'венчур', 'ставка', 'нбрк',
        # Kazakh
        'теңге', 'банк', 'мұнай', 'экономика', 'бизнес', 'салық', 'инвестиция',
        'биржа', 'инфляция', 'бюджет', 'несие', 'сауда',
        # English
        'economy', 'finance', 'bank', 'oil', 'market', 'stock', 'trade', 'gdp',
        'inflation', 'investment', 'crypto', 'bitcoin', 'dollar', 'euro',
        'fed', 'interest rate', 'budget', 'tax', 'business', 'startup',
        'revenue', 'profit', 'loss', 'nasdaq', 's&p', 'dow jones',
    ],
    'cat_tech': [
        # Russian
        'технологии', 'смартфон', 'интернет', 'разработка', 'цифровизация',
        'искусственный интеллект', 'нейросеть', 'программирование', 'приложение',
        'кибербезопасность', 'хакер', 'чип', 'процессор', 'облако', 'блокчейн',
        'робот', 'дрон', 'квантовый', 'вирус', 'платформа', 'гаджет',
        # Kazakh
        'технология', 'смартфон', 'интернет', 'жасанды интеллект', 'цифрлық',
        'бағдарлама', 'қосымша',
        # English
        'technology', 'tech', 'software', 'hardware', 'ai', 'artificial intelligence',
        'machine learning', 'cybersecurity', 'hack', 'chip', 'processor', 'cloud',
        'blockchain', 'robot', 'drone', 'quantum', 'app', 'gadget', 'device',
        'apple', 'google', 'microsoft', 'meta', 'openai', 'samsung', 'nvidia',
        'smartphone', 'laptop', 'iphone', 'android', 'chatgpt', 'gpt',
    ],
    'cat_auto': [
        # Russian
        'автомобиль', 'авто', 'машина', 'двигатель', 'электромобиль', 'гибрид',
        'мотоцикл', 'шины', 'салон', 'кузов', 'трансмиссия', 'дтп', 'водитель',
        'парковка', 'штраф', 'гаи', 'пдд', 'автосалон', 'автопром',
        # Kazakh
        'автомобиль', 'машина', 'электромобиль', 'жол', 'жүргізуші',
        # English
        'car', 'vehicle', 'auto', 'automotive', 'electric vehicle', 'ev', 'hybrid',
        'motorcycle', 'truck', 'suv', 'engine', 'fuel', 'tesla', 'ford',
        'toyota', 'bmw', 'mercedes', 'volkswagen', 'audi', 'ferrari', 'lamborghini',
        'driving', 'crash', 'accident', 'traffic',
    ],
    'cat_world': [
        # Russian
        'война', 'конфликт', 'санкции', 'оон', 'нато', 'дипломатия', 'посол',
        'международный', 'геополитика', 'кризис', 'переговоры', 'договор', 'визит',
        'сша', 'европа', 'китай', 'россия', 'израиль', 'украина', 'иран', 'турция',
        'ближний восток', 'азия', 'африка', 'латинская америка',
        # Kazakh
        'соғыс', 'халықаралық', 'дипломатия', 'келіссөз', 'дүние жүзі',
        # English
        'war', 'conflict', 'sanctions', 'nato', 'un', 'united nations', 'diplomacy',
        'ambassador', 'international', 'geopolitics', 'crisis', 'treaty', 'summit',
        'world', 'global', 'foreign', 'usa', 'europe', 'china', 'russia',
        'israel', 'ukraine', 'iran', 'middle east', 'asia', 'africa',
    ],
    'cat_culture': [
        'культура', 'кино', 'фильм', 'музыка', 'концерт', 'фестиваль', 'театр',
        'выставка', 'искусство', 'звезды', 'шоу-бизнес', 'актер', 'певец',
        'режиссер', 'книга', 'литература', 'танец', 'мода', 'дизайн',
        'мәдениет', 'кино', 'музыка', 'театр', 'өнер', 'концерт',
        'culture', 'movie', 'film', 'music', 'concert', 'festival', 'theater',
        'exhibition', 'art', 'celebrity', 'actor', 'singer', 'director',
        'book', 'literature', 'fashion', 'design', 'award', 'oscar', 'grammy', 'netflix', 'spotify',
    ],
    'cat_health': [
        'здоровье', 'медицина', 'врач', 'больница', 'лечение', 'болезнь', 'вирус',
        'вакцина', 'пандемия', 'диета', 'фитнес', 'спа', 'психология',
        'денсаулық', 'дәрігер', 'ауруxана', 'дәрі', 'вакцина',
        'health', 'medicine', 'doctor', 'hospital', 'treatment', 'disease', 'virus',
        'vaccine', 'pandemic', 'diet', 'fitness', 'mental health', 'pharmacy', 'drug',
        'covid', 'surgery', 'cancer', 'diabetes', 'nutrition',
    ],
    'cat_science': [
        'наука', 'исследование', 'открытие', 'космос', 'физика', 'химия',
        'биология', 'астрономия', 'климат', 'эксперимент', 'ученые',
        'ғылым', 'зерттеу', 'ашылым', 'ғарыш', 'физика',
        'science', 'research', 'discovery', 'space', 'physics', 'chemistry',
        'biology', 'astronomy', 'climate', 'experiment', 'scientists', 'nasa',
        'spacex', 'study', 'universe', 'dna', 'gene',
    ],
    'cat_travel': [
        'путешествие', 'туризм', 'отдых', 'отпуск', 'виза', 'аэропорт',
        'отель', 'курорт', 'экскурсия', 'тур', 'авиабилет',
        'саяхат', 'туризм', 'демалыс', 'виза', 'қонақүй',
        'travel', 'tourism', 'vacation', 'holiday', 'visa', 'airport',
        'hotel', 'resort', 'tour', 'flight', 'destination', 'cruise',
    ],
    'cat_food': [
        'еда', 'ресторан', 'кулинария', 'рецепт', 'кухня', 'блюдо', 'напиток',
        'кафе', 'бар', 'повар', 'гастрономия', 'продукты',
        'тамақ', 'мейрамхана', 'рецепт', 'ас', 'асхана',
        'food', 'restaurant', 'recipe', 'cuisine', 'dish', 'drink',
        'cafe', 'chef', 'gastronomy', 'menu', 'cooking', 'street food',
    ],
    'cat_education': [
        'образование', 'школа', 'университет', 'студент', 'учитель',
        'наука', 'грант', 'ент', 'егэ', 'диплом', 'профессия',
        'білім', 'мектеп', 'университет', 'студент', 'ұстаз', 'грант', 'ент',
        'education', 'school', 'university', 'student', 'teacher',
        'grant', 'scholarship', 'degree', 'exam', 'college', 'learning',
    ],
    'cat_environment': [
        'экология', 'природа', 'климат', 'загрязнение', 'озеро', 'лес',
        'зеленая энергия', 'солнечная', 'ветер', 'выброс', 'углерод',
        'экология', 'табиғат', 'климат', 'ластану', 'орман',
        'ecology', 'environment', 'nature', 'climate change', 'pollution', 'green',
        'renewable', 'solar', 'wind', 'emission', 'carbon', 'forest', 'ocean',
    ],
    'cat_finance': [
        'банк', 'кредит', 'депозит', 'ставка', 'ипотека', 'нбрк',
        'пенсия', 'страхование', 'инвестиция', 'акции', 'фондовый',
        'банк', 'несие', 'депозит', 'ипотека', 'зейнетақы', 'сақтандыру',
        'bank', 'credit', 'deposit', 'mortgage', 'pension', 'insurance',
        'investment', 'stock market', 'bonds', 'interest rate', 'fintech', 'loan',
    ],
    'cat_entertainment': [
        'развлечения', 'игра', 'геймер', 'казино', 'шоу', 'концерт',
        'видеоигра', 'стриминг', 'youtube', 'tiktok', 'блогер',
        'ойын-сауық', 'ойын', 'шоу', 'концерт', 'блогер',
        'entertainment', 'game', 'gamer', 'gaming', 'show', 'streaming',
        'youtube', 'tiktok', 'blogger', 'influencer', 'esports', 'twitch',
    ],
    'cat_society': [
        'общество', 'социальный', 'молодежь', 'женщины', 'права', 'закон',
        'миграция', 'демография', 'семья', 'дети', 'пенсионер',
        'қоғам', 'әлеуметтік', 'жастар', 'әйелдер', 'отбасы', 'балалар',
        'society', 'social', 'youth', 'women', 'rights', 'law',
        'migration', 'demographics', 'family', 'children', 'elderly',
    ],
    'cat_crime': [
        'происшествие', 'авария', 'уголовное', 'задержан', 'мошенничество',
        'ограбление', 'убийство', 'арест', 'суд', 'полиция', 'коррупция',
        'оқиға', 'авария', 'қылмыс', 'тұтқындалды', 'алаяқтық', 'сот',
        'crime', 'accident', 'arrest', 'fraud', 'robbery', 'murder',
        'court', 'police', 'corruption', 'investigation', 'criminal',
    ],
}

# Source name → category mapping (case-insensitive substrings)
SOURCE_CATEGORY_MAP = {
    'cat_tech': ['verge', 'techcrunch', 'wired', 'ars technica', 'engadget', 'gizmodo',
                 'tech', 'digit', 'habr', 'ict', '4pda'],
    'cat_auto': ['motor1', 'autoblog', 'auto', 'drive', 'autonews', 'cars', 'avto', 'kolesa'],
    'cat_sport': ['sport', 'чемпионат', 'sovsport', 'sports', 'goal', 'transfermarkt', 'vesti.kz'],
    'cat_economy': ['finanz', 'bloomberg', 'reuters', 'forbes', 'rbc', 'banki', 'economy', 'kapital', 'lsm'],
    'cat_world': ['bbc', 'cnn', 'reuters', 'ap news', 'al jazeera', 'euronews', 'vlast'],
    'cat_culture': ['afisha', 'culture', 'film', 'cinema', 'kinopoisk', 'nur.kz', 'steppe'],
    'cat_politics': ['politik', 'politik.kz', 'kapital', 'zakon.kz', 'inform.kz'],
    'cat_health': ['health', 'медицин', 'zdrav', 'med', 'wellness'],
    'cat_science': ['science', 'nauka', 'nasa', 'space', 'techno'],
    'cat_finance': ['banki', 'finance', 'invest', 'fond'],
    'cat_society': ['society', 'social', 'общество'],
    'cat_crime': ['crime', 'police', 'происшест', 'полиц'],
}

# RSS category/tag → our category mapping (case-insensitive)
RSS_TAG_MAP = {
    'cat_politics': ['politics', 'политика', 'government', 'правительство', 'выборы', 'election'],
    'cat_sport': ['sport', 'sports', 'спорт', 'football', 'soccer', 'basketball'],
    'cat_economy': ['economy', 'finance', 'business', 'экономика', 'финансы', 'бизнес', 'money'],
    'cat_tech': ['technology', 'tech', 'технологии', 'it'],
    'cat_auto': ['auto', 'cars', 'automotive', 'авто', 'автомобили'],
    'cat_world': ['world', 'international', 'мир', 'международное'],
    'cat_culture': ['culture', 'entertainment', 'arts', 'культура', 'кино', 'музыка'],
    'cat_health': ['health', 'медицина', 'здоровье', 'medicine'],
    'cat_science': ['science', 'наука', 'space', 'космос', 'research'],
    'cat_travel': ['travel', 'туризм', 'tourism', 'путешествия'],
    'cat_food': ['food', 'еда', 'recipe', 'рецепт'],
    'cat_education': ['education', 'образование', 'school', 'university'],
    'cat_environment': ['environment', 'экология', 'climate', 'климат'],
    'cat_finance': ['finance', 'финансы', 'bank', 'банк', 'invest'],
    'cat_entertainment': ['entertainment', 'развлечения', 'gaming', 'игры'],
    'cat_society': ['society', 'общество', 'social'],
    'cat_crime': ['crime', 'происшествие', 'police', 'полиция'],
}


def determine_category(title, content, source_name, rss_tags=None):
    """
    Categorize news using a weighted scoring system.
    
    Priority order:
    1. RSS tags/categories (most reliable signal)
    2. Source name mapping  
    3. Title keyword scoring (weight x3)
    4. Content keyword scoring (weight x1)
    
    Returns the category with the highest score.
    """
    title = str(title) if title else ""
    content = str(content) if content else ""
    source_name = str(source_name) if source_name else ""
    
    # --- 1. RSS tags (strongest signal) ---
    if rss_tags:
        tags_lower = [str(t).lower() for t in rss_tags]
        for cat_code, tag_patterns in RSS_TAG_MAP.items():
            for tag in tags_lower:
                if any(p in tag for p in tag_patterns):
                    return cat_code

    # --- 2. Source name matching ---
    source_lower = source_name.lower()
    for cat_code, source_patterns in SOURCE_CATEGORY_MAP.items():
        if any(p in source_lower for p in source_patterns):
            return cat_code

    # --- 3. Weighted keyword scoring (title x3, content x1) ---
    title_lower = title.lower()
    # Use first 1500 chars of content to avoid over-weighting long texts
    content_lower = content[:1500].lower()

    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}

    for cat_code, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                scores[cat_code] += 3   # Title match = 3 points
            if kw in content_lower:
                scores[cat_code] += 1   # Content match = 1 point

    best_cat = max(scores, key=lambda c: scores[c])
    if scores[best_cat] > 0:
        return best_cat

    return 'cat_general'


def get_image_from_rss_entry(entry):
    """
    Барлық танымал RSS форматтарынан сурет URL-ін шығарып алу.
    Қолдайтын форматтар:
      - media:content / media:thumbnail
      - links (type=image/*)
      - enclosure (type=image/*)
      - media:group > media:content
      - itunes:image
      - summary/description ішіндегі <img src=...>
      - content:encoded ішіндегі <img src=...>
    """
    # 1. media:content — ең жиі кездесетін формат
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            url = media.get('url', '')
            if url and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                return url
        # Кеңейтімі жоқ болса да қабылдаймыз
        for media in entry.media_content:
            url = media.get('url', '')
            if url:
                return url

    # 2. media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            url = thumb.get('url', '')
            if url:
                return url

    # 3. links ішінен image типіндегі сілтеме
    if hasattr(entry, 'links') and entry.links:
        for link in entry.links:
            link_type = link.get('type', '')
            if 'image' in link_type:
                return link.get('href', '')

    # 4. enclosure (audio/video емес, image болса)
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            enc_type = enc.get('type', '')
            if 'image' in enc_type:
                return enc.get('href', '') or enc.get('url', '')

    # 5. itunes:image
    if hasattr(entry, 'image') and entry.image:
        img = entry.image
        if isinstance(img, dict):
            return img.get('href', '') or img.get('url', '')

    # 6. summary немесе description ішіндегі <img> тегі
    for field in ['summary', 'description', 'content']:
        html_text = ''
        if field == 'content' and hasattr(entry, 'content') and entry.content:
            html_text = entry.content[0].get('value', '')
        else:
            html_text = entry.get(field, '') or ''

        if '<img' in html_text:
            # data-src немесе src іздеу
            match = re.search(r'<img[^>]+(?:data-src|src)\s*=\s*["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            if match:
                url = match.group(1)
                if url and not url.startswith('data:'):
                    return url

    return None

# Fallback User-Agent тізімі (кейбір сайттар бірінші UA-ны блоктайды)
_UA_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
]

def download_image(image_url, upload_folder, source_url=None):
    """
    Сурет URL-ін жүктеп, жергілікті файлға сақтайды.
    - Салыстырмалы URL-дерді толық URL-ге айналдырады
    - '//' протоколсыз сілтемелерді дүзетеді
    - 3 түрлі User-Agent-пен байқап көреді (блоктаудан қашу үшін)
    - Content-type тексеруі жұмсартылған (200 болса — сақтайды)
    """
    try:
        os.makedirs(upload_folder, exist_ok=True)
        if not image_url:
            return None

        image_url = image_url.strip()

        # Protocol-relative URL: //example.com/image.jpg
        if image_url.startswith('//'):
            image_url = 'https:' + image_url

        # Relative URL: /images/photo.jpg — source_url-дің доменін қолдану
        if image_url.startswith('/') and source_url:
            from urllib.parse import urlparse
            parsed = urlparse(source_url)
            image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"

        # Толық URL емес болса (http/https жоқ) — өткізіп жіберу
        if not image_url.startswith(('http://', 'https://')):
            return None

        # URL-дан кеңейтімді анықтау
        url_lower = image_url.lower().split('?')[0]  # query string-ті алып тастау
        ext = 'jpg'
        if url_lower.endswith('.png'):
            ext = 'png'
        elif url_lower.endswith('.webp'):
            ext = 'webp'
        elif url_lower.endswith('.gif'):
            ext = 'gif'
        elif url_lower.endswith('.jpeg'):
            ext = 'jpg'

        response = None
        # 3 UA-мен байқап көру
        for ua in _UA_LIST:
            try:
                headers = {
                    'User-Agent': ua,
                    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                    'Referer': 'https://www.google.com/',
                    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                }
                r = requests.get(image_url, headers=headers, timeout=12, stream=True)
                if r.status_code == 200:
                    response = r
                    break
                elif r.status_code in (403, 401):
                    continue  # Келесі UA-мен байқау
            except Exception:
                continue

        if response is None:
            return None

        content_type = response.headers.get('content-type', '').lower()

        # Content-type-тен кеңейтімді нақтылау (URL-ден алынғанды жазып отыру)
        if 'png' in content_type:
            ext = 'png'
        elif 'webp' in content_type:
            ext = 'webp'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'

        # Мазмұнды оқып тексеру (content-type болмаса да қабылдаймыз)
        # Тек HTML/text болса ғана өткізіп жіберу
        if content_type and any(t in content_type for t in ['text/html', 'text/plain', 'application/json', 'application/xml']):
            return None

        content = b''
        for chunk in response.iter_content(8192):
            content += chunk
            if len(content) > 10 * 1024 * 1024:  # 10 MB max
                break

        # Ең болмаса 1 KB болу керек (валидті сурет)
        if len(content) < 1024:
            return None

        # Magic bytes арқылы суретті тексеру
        if content[:4] == b'\x89PNG':
            ext = 'png'
        elif content[:2] in (b'\xff\xd8', b'\xff\xe0', b'\xff\xe1'):
            ext = 'jpg'
        elif content[:4] == b'RIFF' and content[8:12] == b'WEBP':
            ext = 'webp'
        elif content[:6] in (b'GIF87a', b'GIF89a'):
            ext = 'gif'
        elif b'<html' in content[:100].lower() or b'<!doctype' in content[:100].lower():
            return None  # HTML беті, сурет емес

        filename = f"news_{uuid.uuid4().hex[:12]}.{ext}"
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filename

    except Exception as e:
        print(f"  [Error Image]: {e}")
    return None

import trafilatura

def extract_full_content(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/'
            }
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=20)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                downloaded = response.text
                
        content = ""
        image_url = None
        
        if downloaded:
            soup = BeautifulSoup(downloaded, 'html.parser')
            
            # Custom Extraction for Tengrinews to preserve their specific formatting (blue notes)
            if 'tengrinews.kz' in url:
                article_div = soup.find('div', class_='tn-news-text')
                if article_div:
                    for s in article_div.select('script, style, .tn-social-share'):
                        s.extract()
                    content = str(article_div)
            
            if not content:
                # Trafilatura extract as HTML to keep images and structure
                html_content = trafilatura.extract(downloaded, output_format='html', include_images=True, include_links=True, favor_precision=False, favor_recall=True)
                if html_content:
                    content = html_content
                else:
                    # Fallback to plain text if HTML extraction fails
                    content = trafilatura.extract(downloaded, include_images=False, include_links=False, favor_precision=False, favor_recall=True)
            
            # Find the main image from meta tags
            meta_og = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
            meta_tw = soup.find('meta', property='twitter:image') or soup.find('meta', attrs={'name': 'twitter:image'})
            
            if meta_og and meta_og.get('content'):
                image_url = meta_og.get('content')
            elif meta_tw and meta_tw.get('content'):
                image_url = meta_tw.get('content')
                
            # Extract YouTube iframes and append them to the content if they are missing
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'youtube.com' in src or 'youtu.be' in src:
                    # Check if it's already in the content
                    if content and src not in content:
                        iframe_html = f'<div class="ratio ratio-16x9 my-4"><iframe src="{src}" allowfullscreen></iframe></div>'
                        content += iframe_html
        if content:
            soup_clean = BeautifulSoup(content, 'html.parser')
            
            # Remove bad tags completely
            for s in soup_clean(['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'nav', 'aside', 'form', 'button', 'svg', 'table']):
                s.decompose()
                
            # Unwrap layout tags that are unnecessary but keep their content
            for tag in soup_clean.find_all(['div', 'span', 'article', 'section', 'main', 'time']):
                tag.unwrap()
                
            # Allow only these tags
            allowed_tags = ['p', 'b', 'strong', 'i', 'em', 'br', 'ul', 'ol', 'li', 'h2', 'h3', 'h4', 'blockquote', 'img', 'figure', 'figcaption', 'iframe', 'a', 'q']
            
            for tag in soup_clean.find_all(True):
                if tag.name not in allowed_tags:
                    tag.unwrap()
                else:
                    # Clean attributes
                    attrs = {}
                    if tag.name == 'img':
                        # Handle src and lazy loading
                        src = tag.get('src') or tag.get('data-src') or ''
                        if src:
                            attrs['src'] = src
                        if tag.has_attr('alt'):
                            attrs['alt'] = tag['alt']
                        # Add bootstrap styling for uniform images
                        attrs['class'] = 'img-fluid rounded my-3 w-100 shadow-sm'
                    elif tag.name == 'iframe':
                        if tag.has_attr('src'):
                            attrs['src'] = tag['src']
                        attrs['allowfullscreen'] = 'true'
                        attrs['class'] = 'w-100 rounded my-3'
                        attrs['style'] = 'min-height: 400px;'
                    elif tag.name == 'a':
                        if tag.has_attr('href'):
                            attrs['href'] = tag['href']
                        attrs['target'] = '_blank'
                    elif tag.name == 'figcaption':
                        attrs['class'] = 'text-muted small text-center mt-2 fst-italic'
                    elif tag.name == 'blockquote':
                        attrs['class'] = 'border-start border-4 border-primary ps-4 my-4 py-3 bg-primary bg-opacity-10 rounded-end fst-italic text-dark'
                        attrs['style'] = 'border-left-color: #0f62fe !important; font-size: 1.05rem;'
                        
                    tag.attrs = attrs
                    
            import re
            clean_html = str(soup_clean)
            # Remove empty paragraphs
            clean_html = re.sub(r'<p>\s*</p>', '', clean_html)
            # Add ratio for iframe if not wrapped (trafilatura sometimes keeps iframe alone)
            
            content = clean_html
            
        if not content:
            content = ""
            
        return content, image_url
    except Exception as e:
        print(f"  [Error Scraper]: {e}")
        return "", None

def process_source(source_data, app, cats):
    with app.app_context():
        print(f"> SOURCE: {source_data['name']} ({source_data['url']})")
        try:
            feed = feedparser.parse(source_data['url'])
            processed = 0
            news_items = []
            
            for entry in feed.entries:
                if processed >= 10: break # Max 10 per source per run
                link = entry.get('link')
                if not link or News.query.filter_by(original_url=link).first(): 
                    continue
                
                print(f"  * Fetching: {str(entry.get('title', ''))[:40]}...")
                full_text, web_image = extract_full_content(link)
                rss_image = get_image_from_rss_entry(entry)
                
                
                # Make sure full_text is a string
                if full_text is None: full_text = ""

                # ЕГЕР САЙТ БЛОКТАП ТАСТАСА НЕМЕСЕ ҚЫСҚА БОЛСА:
                if not full_text or len(full_text) < 150:
                    # 1. RSS-тің ішіндегі жасырын толық контентті көру ("content:encoded")
                    if 'content' in entry and len(entry.content) > 0:
                        rss_content = entry.content[0].value
                        cleaned_rss = BeautifulSoup(rss_content, "html.parser").get_text(separator='\n\n', strip=True)
                        if len(cleaned_rss) > 150:
                            full_text = cleaned_rss
                    
                    # 2. Ол да болмаса, жай ғана сипаттамасына қарау
                    if not full_text or len(full_text) < 150:
                        summary_text = entry.get('summary', '') or entry.get('description', '') or ""
                        if summary_text:
                            full_text = BeautifulSoup(summary_text, "html.parser").get_text(separator='\n\n', strip=True)

                # Make sure the fallback text is also formatted uniformly
                if full_text and not full_text.startswith('<p>') and not full_text.startswith('<'):
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    clean_html = ""
                    for line in lines:
                        if len(line) > 2:
                            clean_html += f"<p>{line}</p>\n"
                    full_text = clean_html

                if not full_text:
                    print(f"    ! Skipping: Content is empty.")
                    continue
                
                if len(full_text) < 50:
                    print(f"    ! Skipping: Content too short.")
                    continue

                # Суретті жүктеу: алдымен web-тен, болмаса RSS-тен
                image_to_download = web_image or rss_image
                local_img = download_image(image_to_download, app.config['UPLOAD_FOLDER'], source_url=link)
                # web сурет жүктелмесе, RSS суретті жеке байқап көру
                if not local_img and rss_image and rss_image != web_image:
                    local_img = download_image(rss_image, app.config['UPLOAD_FOLDER'], source_url=link)

                
                from app.services.ai_service import AIService

                # Extract RSS tags/categories for better categorization
                rss_tags = []
                if hasattr(entry, 'tags') and entry.tags:
                    rss_tags = [t.get('term', '') or t.get('label', '') for t in entry.tags]
                elif entry.get('category'):
                    rss_tags = [entry.get('category')]

                news_title = str(entry.get('title', 'General'))
                cat_code = determine_category(news_title, full_text, source_data['name'], rss_tags=rss_tags)
                cat_id = cats.get(cat_code, cats.get('cat_general'))
                print(f"    → Category: {cat_code} (score-based)")
                
                # Perform AI enhancement (Translate + Summarize)
                try:
                    ai_data = AIService.process_news(news_title, full_text, source_data['language'])
                except Exception as ai_e:
                    print(f"    ! AI Error: {ai_e}")
                    continue

                import calendar
                import datetime as dt

                pub_date = dt.datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        # feedparser's published_parsed is always in UTC struct_time
                        parsed_time = dt.datetime(*entry.published_parsed[:6])
                        # Use parsed time only if it's within a reasonable range (not broken)
                        if dt.datetime.utcnow() - dt.timedelta(days=7) <= parsed_time <= dt.datetime.utcnow() + dt.timedelta(hours=2):
                            pub_date = parsed_time
                    except Exception as e:
                        print(f"    ! Date Parse Error: {e}")

                item_dict = {
                    'category_id': cat_id,
                    'title_ru': ai_data['title_ru'],
                    'title_kk': ai_data['title_kk'],
                    'title_en': ai_data['title_en'],
                    'content_ru': ai_data['content_ru'],
                    'content_kk': ai_data['content_kk'],
                    'content_en': ai_data['content_en'],
                    'summary_ru': ai_data['summary_ru'],
                    'summary_kk': ai_data['summary_kk'],
                    'summary_en': ai_data['summary_en'],
                    'source_name': source_data['name'],
                    'original_url': link,
                    'image_filename': local_img,
                    'created_at': pub_date
                }
                news_items.append(item_dict)
                processed += 1
            
            return {'source_id': source_data['id'], 'news_items': news_items}
        except Exception as e:
            print(f"  ! Error processing {source_data['name']}: {e}")
            return {'source_id': source_data['id'], 'news_items': []}

def fetch_rss_feeds():
    print(f"== [{datetime.now()}] STARTING PARSER UPDATE ==")
    app = create_app()
    with app.app_context():
        # Ensure categories exist
        for c_code in CATEGORY_KEYWORDS.keys():
            if not Category.query.filter_by(code=c_code).first():
                db.session.add(Category(code=c_code))
        if not Category.query.filter_by(code='cat_general').first():
            db.session.add(Category(code='cat_general'))
            
        # Ensure new sources exist
        new_sources = [
            {'name': 'Zakon.kz', 'url': 'https://www.zakon.kz/rss.xml', 'language': 'ru'},
            {'name': 'Inform.kz Politics', 'url': 'https://www.inform.kz/ru/rss/politics', 'language': 'ru'},
            {'name': 'Tengrinews Politics', 'url': 'https://tengrinews.kz/news/kazakhstan_news/politics/feed/', 'language': 'ru'},
            {'name': 'Sports.kz', 'url': 'https://www.sports.kz/rss', 'language': 'ru'},
            {'name': 'Vesti.kz', 'url': 'https://vesti.kz/rss/', 'language': 'ru'},
            {'name': 'Prosports.kz', 'url': 'https://prosports.kz/rss', 'language': 'ru'},
            {'name': 'Kapital.kz', 'url': 'https://kapital.kz/rss', 'language': 'ru'},
            {'name': 'Forbes.kz', 'url': 'https://forbes.kz/rss', 'language': 'ru'},
            {'name': 'LSM.kz', 'url': 'https://lsm.kz/rss', 'language': 'ru'},
            {'name': 'Er10 Tech', 'url': 'https://er10.kz/feed/', 'language': 'ru'},
            {'name': 'Profit.kz', 'url': 'https://profit.kz/rss/', 'language': 'ru'},
            {'name': 'Bluescreen', 'url': 'https://bluescreen.kz/rss/', 'language': 'ru'},
            {'name': 'Kolesa.kz', 'url': 'https://kolesa.kz/read/news/feed/', 'language': 'ru'},
            {'name': 'Auto.mail.ru', 'url': 'https://auto.mail.ru/rss/news/', 'language': 'ru'},
            {'name': 'Motor.ru', 'url': 'https://motor.ru/export/rss.xml', 'language': 'ru'},
            {'name': 'Tengrinews World', 'url': 'https://tengrinews.kz/world_news/feed/', 'language': 'ru'},
            {'name': 'Informburo', 'url': 'https://informburo.kz/xml/rss.xml', 'language': 'ru'},
            {'name': 'Vlast.kz', 'url': 'https://vlast.kz/rss.xml', 'language': 'ru'},
            {'name': 'The Steppe', 'url': 'https://the-steppe.com/rss', 'language': 'ru'},
            {'name': 'Afisha.ru (Kino)', 'url': 'https://www.afisha.ru/export/rss.xml', 'language': 'ru'},
            {'name': 'Nur.kz (Showbiz)', 'url': 'https://www.nur.kz/rss/showbiz.xml', 'language': 'ru'},
            # New sources for new categories
            {'name': 'Nur.kz Health', 'url': 'https://www.nur.kz/rss/health.xml', 'language': 'ru'},
            {'name': 'Med.kz', 'url': 'https://med.kz/rss', 'language': 'ru'},
            {'name': 'Nauka.kz', 'url': 'https://nauka.kz/rss', 'language': 'ru'},
            {'name': 'National Geographic RU', 'url': 'https://www.nat-geo.ru/rss/all/', 'language': 'ru'},
            {'name': 'Tengrinews Travel', 'url': 'https://tengrinews.kz/travel/feed/', 'language': 'ru'},
            {'name': 'Touristan.kz', 'url': 'https://touristan.kz/rss', 'language': 'ru'},
            {'name': 'Gurman.kz', 'url': 'https://gurman.kz/rss', 'language': 'ru'},
            {'name': 'KursivMedia', 'url': 'https://kursiv.kz/rss', 'language': 'ru'},
            {'name': 'Abai.kz Education', 'url': 'https://abai.kz/rss', 'language': 'ru'},
            {'name': 'Otyrar.kz', 'url': 'https://otyrar.kz/rss', 'language': 'ru'},
            {'name': 'Bnews.kz', 'url': 'https://bnews.kz/rss', 'language': 'ru'},
            {'name': 'Сrime.kz', 'url': 'https://crime.kz/rss', 'language': 'ru'},
        ]
        for s in new_sources:
            if not Source.query.filter((Source.url == s['url']) | (Source.name == s['name'])).first():
                db.session.add(Source(name=s['name'], url=s['url'], language=s['language'], is_active=True))
                
        db.session.commit()
        
        sources = Source.query.filter_by(is_active=True).all()
        source_dicts = [{'id': s.id, 'name': s.name, 'url': s.url, 'language': s.language} for s in sources]
        cats = {c.code: c.id for c in Category.query.all()}
        
        total_added = 0
        # Use ThreadPoolExecutor for concurrent parsing ONLY, DB writes are done sequentially below
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_source, s_data, app, cats) for s_data in source_dicts]
            for future in futures:
                result = future.result()
                source_db = Source.query.get(result['source_id'])
                if source_db:
                    source_db.last_fetched = datetime.utcnow()
                    for item_data in result['news_items']:
                        # Check for existing URL to avoid UNIQUE constraint error
                        existing = News.query.filter_by(original_url=item_data.get('original_url')).first()
                        if existing:
                            continue
                        db.session.add(News(**item_data))
                        total_added += 1
                    try:
                        db.session.commit()
                    except Exception as commit_err:
                        db.session.rollback()
                        print(f"  ! Commit error (skipped): {commit_err}")
                
    print(f"== FINISHED. TOTAL ADDED: {total_added} ==")

if __name__ == "__main__":
    fetch_rss_feeds()
