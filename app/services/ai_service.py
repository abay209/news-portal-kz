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
        
        # deep-translator uses 'ru', 'kk', 'en' which matches our codes
        try:
            # Split text if too long (Google has limits around 5k chars)
            if len(text) > 4000:
                text = text[:4000]
                
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
            return translated if translated is not None else ""
        except Exception as e:
            print(f"[AI Service] Translation Error: {e}")
            return f"{text[:200]}..." # Fallback: original partial text

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

        # 2. Translate Content
        content_ru = content if source_lang == 'ru' else cls.translate_text(content, 'ru', source_lang)
        content_kk = content if source_lang == 'kk' else cls.translate_text(content, 'kk', source_lang)
        content_en = content if source_lang == 'en' else cls.translate_text(content, 'en', source_lang)
        
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
