from flask import Flask, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Fix HTTPS detection behind Railway/Render reverse proxy
    # This ensures url_for generates https:// links for OAuth redirect URIs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    db.init_app(app)
    login_manager.init_app(app)
    
    # Enable WAL mode for SQLite to handle concurrency (only for SQLite)
    with app.app_context():
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            from sqlalchemy import event
            @event.listens_for(db.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes import main
    from app.admin import admin_bp
    from app.auth import auth_bp, init_oauth
    
    init_oauth(app)
    
    app.register_blueprint(main)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Create database tables if they don't exist
    with app.app_context():
        from app import models  # noqa: F401 - ensure all models are imported
        from app.models import Category, User, Source
        db.create_all()
        
        # Init default categories
        if Category.query.count() == 0:
            categories = ['cat_general', 'cat_politics', 'cat_sport', 'cat_economy', 'cat_tech', 'cat_world', 'cat_auto', 'cat_culture']
            for c in categories:
                db.session.add(Category(code=c))
            db.session.commit()
            
        # Init default admin
        if User.query.filter_by(username='admin').first() is None:
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            
        # Init default sources
        if Source.query.count() == 0:
            initial_sources = [
                {'name': 'Tengrinews.kz', 'url': 'https://tengrinews.kz/news.rss', 'lang': 'ru'},
                {'name': 'Nur.kz', 'url': 'https://www.nur.kz/rss/', 'lang': 'ru'},
                {'name': 'Zakon.kz', 'url': 'https://www.zakon.kz/rss/', 'lang': 'ru'},
                {'name': 'Inform.kz', 'url': 'https://www.inform.kz/inform.rss', 'lang': 'ru'},
                {'name': 'BBC World', 'url': 'http://feeds.bbci.co.uk/news/world/rss.xml', 'lang': 'en'},
                {'name': 'The Verge', 'url': 'https://www.theverge.com/rss/index.xml', 'lang': 'en'}
            ]
            for s in initial_sources:
                db.session.add(Source(name=s['name'], url=s['url'], language=s['lang']))
            db.session.commit()

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.template_filter('image_url')
    def get_image_url(filename):
        if not filename: return ''
        if filename.startswith('http://') or filename.startswith('https://'):
            return filename
        from flask import url_for
        return url_for('static', filename='images/uploads/' + filename)

    # Template context processors
    from app.translations import get_translation
    
    @app.context_processor
    def inject_translations():
        def _(key):
            lang = session.get('lang', 'ru')
            return get_translation(lang, key)
        return dict(_=_, current_lang=lambda: session.get('lang', 'ru'))

    @app.context_processor
    def inject_global_vars():
        """Inject globally needed variables into all templates."""
        from app.models import Category, News, Setting
        import re
        
        def get_youtube_embed_url(url):
            if not url: return ""
            match = re.search(r'(?:v=|live/|youtu\.be/|embed/)([A-Za-z0-9_-]{11})', url)
            if match:
                return f"https://www.youtube.com/embed/{match.group(1)}?autoplay=1&mute=1"
            return url

        try:
            categories = Category.query.all()
            ticker_news = News.query.order_by(News.created_at.desc()).limit(8).all()
            settings = {s.key: s.value for s in Setting.query.all()}
            if 'youtube_live_url' in settings:
                settings['youtube_live_url'] = get_youtube_embed_url(settings['youtube_live_url'])
        except Exception:
            categories = []
            ticker_news = []
            settings = {}
        return dict(
            categories=categories,
            current_cat=request.args.get('category'),
            ticker_news=ticker_news,
            settings=settings
        )
        
    return app
