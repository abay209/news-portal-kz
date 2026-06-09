import feedparser
from rss_parser import extract_full_content, get_image_from_rss_entry, download_image
import app
app_instance = app.create_app()
with app_instance.app_context():
    feed = feedparser.parse('https://tengrinews.kz/news/kazakhstan_news/politics/feed/')
    entry = feed.entries[0]
    link = entry.get('link')
    print("Link:", link)
    full_text, web_image = extract_full_content(link)
    rss_image = get_image_from_rss_entry(entry)
    print("Web Image:", web_image)
    print("RSS Image:", rss_image)
    image_to_download = web_image or rss_image
    local_img = download_image(image_to_download, app_instance.config['UPLOAD_FOLDER'], source_url=link)
    print("Downloaded Local Image:", local_img)
