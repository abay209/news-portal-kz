from deep_translator import GoogleTranslator
html = '<p>Hello <b>world</b></p><img src="http://example.com/image.jpg" alt="test image"><figcaption>A nice photo</figcaption>'
translated = GoogleTranslator(source='en', target='ru').translate(html)
print("Original:", html)
print("Translated:", translated)
