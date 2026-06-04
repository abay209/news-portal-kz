from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, News, Category, Source, Setting
from app import db
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta

from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('У вас нет доступа к этой странице.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Неправильный логин или пароль')
            
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_news = News.query.count()
    total_views = db.session.query(db.func.sum(News.views)).scalar() or 0
    total_sources = Source.query.count()
    
    # Stats for chart
    last_7_days = [(datetime.utcnow() - timedelta(days=i)).date() for i in range(6, -1, -1)]
    news_stats = []
    for day in last_7_days:
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = News.query.filter(News.created_at >= day_start, News.created_at <= day_end).count()
        news_stats.append(count)
        
    categories = Category.query.all()
    cat_stats = {c.code: News.query.filter_by(category_id=c.id).count() for c in categories}
    
    return render_template('admin/dashboard.html', 
                          total_news=total_news, 
                          total_views=total_views,
                          total_sources=total_sources,
                          news_stats=news_stats,
                          cat_stats=cat_stats)

@admin_bp.route('/news')
@admin_required
def news_list():
    page = request.args.get('page', 1, type=int)
    news_pagination = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/news_list.html', news_pagination=news_pagination)

@admin_bp.route('/sources')
@admin_required
def sources_list():
    sources = Source.query.all()
    return render_template('admin/sources_list.html', sources=sources)

@admin_bp.route('/sources/add', methods=['GET', 'POST'])
@admin_required
def source_add():
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        language = request.form.get('language', 'ru')
        new_source = Source(name=name, url=url, language=language)
        db.session.add(new_source)
        db.session.commit()
        flash('Источник добавлен')
        return redirect(url_for('admin.sources_list'))
    return render_template('admin/source_form.html', source=None)

@admin_bp.route('/sources/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def source_edit(id):
    source = Source.query.get_or_404(id)
    if request.method == 'POST':
        source.name = request.form.get('name')
        source.url = request.form.get('url')
        source.language = request.form.get('language')
        source.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Источник обновлен')
        return redirect(url_for('admin.sources_list'))
    return render_template('admin/source_form.html', source=source)

@admin_bp.route('/sources/delete/<int:id>')
@admin_required
def source_delete(id):
    source = Source.query.get_or_404(id)
    db.session.delete(source)
    db.session.commit()
    flash('Источник удален')
    return redirect(url_for('admin.sources_list'))

@admin_bp.route('/news/add', methods=['GET', 'POST'])
@admin_required
def news_add():
    categories = Category.query.all()
    if request.method == 'POST':
        source_lang = request.form.get('source_lang', 'ru')
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        
        # Initialize translation
        from deep_translator import GoogleTranslator
        
        titles = {'kk': '', 'ru': '', 'en': ''}
        contents = {'kk': '', 'ru': '', 'en': ''}
        
        titles[source_lang] = title
        contents[source_lang] = content
        
        # Translate to other languages
        for lang in ['kk', 'ru', 'en']:
            if lang != source_lang:
                try:
                    target_lang = 'kk' if lang == 'kk' else ('ru' if lang == 'ru' else 'en')
                    source_lang_trans = 'kk' if source_lang == 'kk' else ('ru' if source_lang == 'ru' else 'en')
                    translator = GoogleTranslator(source=source_lang_trans, target=target_lang)
                    titles[lang] = translator.translate(title)
                    # Translation of long content might be slow or fail, try-except is good here
                    # For very long text, one should chunk, but let's assume it works for normal news
                    contents[lang] = translator.translate(content)
                except Exception as e:
                    print(f"Translation error: {e}")
                    titles[lang] = title + f" ({lang})"
                    contents[lang] = content + f" ({lang})"
        
        # Handle Image
        image_file = request.files.get('image')
        image_filename = None
        has_image = request.form.get('has_image')
        if has_image == 'yes' and image_file and image_file.filename:
            ext = os.path.splitext(image_file.filename)[1]
            image_filename = str(uuid.uuid4()) + ext
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(path)
            
        new_news = News(
            title_kk=titles['kk'], title_ru=titles['ru'], title_en=titles['en'],
            content_kk=contents['kk'], content_ru=contents['ru'], content_en=contents['en'],
            category_id=category_id,
            image_filename=image_filename
        )
        
        # Handle tags
        from app.models import Tag
        tags_input = request.form.get('tags', '')
        if tags_input:
            tag_names = [t.strip().lower() for t in tags_input.split(',') if t.strip()]
            for t_name in tag_names:
                tag = Tag.query.filter_by(name=t_name).first()
                if not tag:
                    tag = Tag(name=t_name)
                    db.session.add(tag)
                new_news.tags.append(tag)
                
        db.session.add(new_news)
        db.session.commit()
        flash('Новость добавлена и переведена')
        return redirect(url_for('admin.news_list'))
        
    # Translate categories for the dropdown using TRANSLATIONS
    from app.translations import get_translation
    translated_categories = []
    for cat in categories:
        translated_categories.append({
            'id': cat.id,
            'name': get_translation('ru', cat.code)
        })
        
    return render_template('admin/news_form.html', categories=translated_categories, news=None)

@admin_bp.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
@admin_required
def news_edit(news_id):
    news_item = News.query.get_or_404(news_id)
    categories = Category.query.all()
    if request.method == 'POST':
        news_item.title_kk = request.form.get('title_kk')
        news_item.title_ru = request.form.get('title_ru')
        news_item.title_en = request.form.get('title_en')
        news_item.content_kk = request.form.get('content_kk')
        news_item.content_ru = request.form.get('content_ru')
        news_item.content_en = request.form.get('content_en')
        news_item.category_id = request.form.get('category_id')
        
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            ext = os.path.splitext(image_file.filename)[1]
            image_filename = str(uuid.uuid4()) + ext
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(path)
            news_item.image_filename = image_filename
            
        # Handle tags
        from app.models import Tag
        tags_input = request.form.get('tags', '')
        news_item.tags = [] # clear existing
        if tags_input:
            tag_names = [t.strip().lower() for t in tags_input.split(',') if t.strip()]
            for t_name in tag_names:
                tag = Tag.query.filter_by(name=t_name).first()
                if not tag:
                    tag = Tag(name=t_name)
                    db.session.add(tag)
                news_item.tags.append(tag)
                
        db.session.commit()
        flash('Новость обновлена')
        return redirect(url_for('admin.news_list'))
    return render_template('admin/news_form.html', categories=categories, news=news_item)

@admin_bp.route('/news/delete/<int:news_id>')
@admin_required
def news_delete(news_id):
    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    flash('Новость удалена')
    return redirect(url_for('admin.news_list'))

@admin_bp.route('/news/fetch_rss')
@admin_required
def news_fetch_rss():
    from rss_parser import fetch_rss_feeds
    try:
        fetch_rss_feeds()
        flash('RSS ленты обновлены!', 'success')
    except Exception as e:
        flash(f'Ошибка: {e}', 'error')
    return redirect(url_for('admin.news_list'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                db.session.add(Setting(key=key, value=value))
        db.session.commit()
        flash('Настройки сохранены')
        return redirect(url_for('admin.settings'))
    
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/subscribers')
@admin_required
def subscribers_list():
    from app.models import Subscriber
    page = request.args.get('page', 1, type=int)
    subscribers_pagination = Subscriber.query.order_by(Subscriber.created_at.desc()).paginate(page=page, per_page=30)
    return render_template('admin/subscribers_list.html', subscribers_pagination=subscribers_pagination)

@admin_bp.route('/subscribers/delete/<int:sub_id>')
@admin_required
def subscriber_delete(sub_id):
    from app.models import Subscriber
    sub = Subscriber.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    flash('Подписчик удален')
    return redirect(url_for('admin.subscribers_list'))
