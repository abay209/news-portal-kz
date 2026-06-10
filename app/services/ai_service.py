from deep_translator import GoogleTranslator
import re

class AIService:
    @staticmethod
    def translate_text(text, target_lang='kk', source_lang='auto'):
        """
        Translates text to the target language using Google Translator.
        target_lang can be 'kk' (Kazakh), 'ru' (Russian), or 'en' (English).
        """
        if not text:
            return ""
        
        try:
            if len(text) <= 4000:
                translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
                return translated if translated is not None else ""
            else:
                chunks = []
                current_chunk = ""
                for word in text.split(' '):
                    if len(current_chunk) + len(word) > 3500:
                        chunks.append(current_chunk)
                        current_chunk = word + " "
                    else:
                        current_chunk += word + " "
                if current_chunk:
                    chunks.append(current_chunk)
                
                translated_chunks = []
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                for chunk in chunks:
                    res = translator.translate(chunk)
                    if res: translated_chunks.append(res)
                return " ".join(translated_chunks)
        except Exception as e:
            print(f"[AI Service] Translation Error: {e}")
            return text

    @classmethod
    def translate_html(cls, html_content, target_lang='kk', source_lang='auto'):
        if not html_content:
            return ""
            
        from bs4 import BeautifulSoup, NavigableString
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. HTML -> тегтерді сақта, таза мәтін шығар
        text_nodes = []
        texts_to_translate = []
        for element in soup.find_all(string=True):
            if element.parent.name not in ['script', 'style'] and element.strip():
                text_nodes.append(element)
                # Remove newlines to avoid breaking the separator
                clean_text = re.sub(r'\s+', ' ', element).strip()
                texts_to_translate.append(clean_text)
                
        if not text_nodes:
            return html_content
            
        # 2. Аудар (біріктіріп жібереміз)
        separator = "\n\n"
        full_text = separator.join(texts_to_translate)
        translated_full = cls.translate_text(full_text, target_lang, source_lang)
        
        # 3. Тегтерді қайта қос (split арқылы мәтіндерді орнына қою)
        translated_texts = [t.strip() for t in re.split(r'\n+', translated_full)]
        
        for i, node in enumerate(text_nodes):
            if i < len(translated_texts) and translated_texts[i].strip():
                node.replace_with(NavigableString(translated_texts[i]))
                
        return str(soup)

    @staticmethod
    def summarize_text(text, lang='ru'):
        """
        Generates a summary of the text. 
        For now, uses an extractive approach (first 3 sentences).
        Can be upgraded to use DeepSeek/Gemini API easily.
        """
        if not text:
            return ""
            
        # Basic extractive summary
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary = " ".join(sentences[:3])
        
        # If text is too short, just return it
        if len(sentences) <= 3:
            return text
            
        return summary

    @classmethod
    def process_news(cls, title, content, source_lang='ru'):
        """
        Processes a single news item: translates title/content and generates summaries.
        Returns a dict with all language versions.
        """
        print(f"[AI Engine] Processing: {title[:50]}...")
        
        # 1. Translate Title
        title_ru = title if source_lang == 'ru' else cls.translate_text(title, 'ru', source_lang)
        title_kk = title if source_lang == 'kk' else cls.translate_text(title, 'kk', source_lang)
        title_en = title if source_lang == 'en' else cls.translate_text(title, 'en', source_lang)

        # 2. Translate Content using translate_html to preserve images and avoid tag corruption
        content_ru = content if source_lang == 'ru' else cls.translate_html(content, 'ru', source_lang)
        content_kk = content if source_lang == 'kk' else cls.translate_html(content, 'kk', source_lang)
        content_en = content if source_lang == 'en' else cls.translate_html(content, 'en', source_lang)
        
        # 3. Generate Summaries
        summary_ru = cls.summarize_text(content_ru, 'ru')
        summary_kk = cls.summarize_text(content_kk, 'kk')
        summary_en = cls.summarize_text(content_en, 'en')

        return {
            'title_ru': title_ru,
            'title_kk': title_kk,
            'title_en': title_en,
            'content_ru': content_ru,
            'content_kk': content_kk,
            'content_en': content_en,
            'summary_ru': summary_ru,
            'summary_kk': summary_kk,
            'summary_en': summary_en
        }
