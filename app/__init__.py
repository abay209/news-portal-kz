from flask import Flask, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

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
