import requests
from bs4 import BeautifulSoup
import re

url = 'https://tengrinews.kz/news/kazakhstan_news/politics/feed/'
r = requests.get(url)
soup = BeautifulSoup(r.content, 'xml')
link = soup.find('item').find('link').text

print("Testing link:", link)

headers = {
    'User-Agent': 'Mozilla/5.0',
}
r2 = requests.get(link, headers=headers)
html = r2.text

soup_article = BeautifulSoup(html, 'html.parser')
article_div = soup_article.find('div', class_='tn-news-text')
if article_div:
    for s in article_div.select('script, style, .tn-social-share'):
        s.extract()
    content = str(article_div)
else:
    content = ""

print("--- Original Content length:", len(content))

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
                src = tag.get('src') or tag.get('data-src') or ''
                if src:
                    attrs['src'] = src
                if tag.has_attr('alt'):
                    attrs['alt'] = tag['alt']
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
            
    clean_html = str(soup_clean)
    clean_html = re.sub(r'<p>\s*</p>', '', clean_html)
    print("--- Clean HTML length:", len(clean_html))
    print(clean_html[:1000])
