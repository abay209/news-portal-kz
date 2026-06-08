from flask import Blueprint, render_template, request, session, redirect, jsonify, url_for
from flask_login import current_user
from app.models import News, Category, Comment, Bookmark, Like, Setting
from app import db
from sqlalchemy import or_

main = Blueprint('main', __name__)

@main.route('/fix-news')
def fix_news():
    # 1. Clear all old news to force re-download of photos
    News.query.delete()
    # 2. Add default Live Stream setting
    if Setting.query.filter_by(key='youtube_live_url').first() is None:
        db.session.add(Setting(key='youtube_live_url', value='https://www.youtube.com/embed/gCNeDWCI0vo?autoplay=1&mute=1'))
    db.session.commit()
    # 3. Fetch fresh news
    from rss_parser import fetch_rss_feeds
    fetch_rss_feeds()
    return "Барлығы жөнделді! Басты бетке қайта беріңіз: <a href='/'>Басты бет</a>"

@main.route('/')
def index():
    # Make sure lang is set
    if 'lang' not in session:
        session['lang'] = 'ru'
        
    category_code = request.args.get('category')
    search_query = request.args.get('q')
    
    query = News.query.filter(
        News.image_filename.isnot(None),
        News.image_filename != ''
    ).order_by(News.created_at.desc())
    
    if category_code:
        cat = Category.query.filter_by(code=category_code).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
            
    if search_query:
        # Search in all language titles and contents
        term = f"%{search_query}%"
        query = query.filter(
            or_(
                News.title_ru.ilike(term),
                News.title_kk.ilike(term),
                News.title_en.ilike(term),
                News.content_ru.ilike(term),
                News.content_en.ilike(term),
                News.content_kk.ilike(term)
            )
        )
        
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    news_list = pagination.items
    
    # If we are on the main landing page (no filter, no search, first page), 
    # we want to provide news grouped by category for the "newspaper" layout.
    news_by_category = {}
    if not category_code and not search_query and page == 1:
        categories = Category.query.all()
        for cat in categories:
            # Get latest 4 news for each category
            news_by_category[cat.code] = News.query.filter(
                News.category_id == cat.id,
                News.image_filename.isnot(None),
                News.image_filename != ''
            ).order_by(News.created_at.desc()).limit(4).all()
    
    # Hero section үшін тек фотолы жаңалықтар
    hero_news = []
    if not category_code and not search_query and page == 1:
        hero_news = News.query.filter(
            News.image_filename.isnot(None),
            News.image_filename != ''
        ).order_by(News.created_at.desc()).limit(3).all()
    
    return render_template('index.html', 
                          news_list=news_list,
                          pagination=pagination,
                          search_query=search_query,
                          news_by_category=news_by_category,
                          hero_news=hero_news)

@main.route('/news/<int:news_id>')
def news_detail(news_id):
    news_item = News.query.get_or_404(news_id)
    # Increment views
    news_item.views += 1
    
    # Save view history
    import uuid
    from app.models import ViewHistory
    
    session_id = session.get('view_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['view_session_id'] = session_id
        
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Optional: avoid duplicate views from same user/session for the same news within a short time
    # For now, let's just insert
    view_history = ViewHistory(user_id=user_id, session_id=session_id, news_id=news_item.id)
    db.session.add(view_history)
    
    db.session.commit()
    
    comments = Comment.query.filter_by(news_id=news_id).order_by(Comment.created_at.desc()).all()
    
    # Check like/bookmark status
    user_liked = False
    user_bookmarked = False
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, news_id=news_id).first() is not None
        user_bookmarked = Bookmark.query.filter_by(user_id=current_user.id, news_id=news_id).first() is not None
        
    likes_count = Like.query.filter_by(news_id=news_id).count()
    # Sidebar: latest 6 news (trending)
    latest_news = News.query.filter(News.id != news_id).order_by(News.views.desc()).limit(6).all()
    # Sidebar: related news from same category (exclude current)
    related_news = News.query.filter(
        News.category_id == news_item.category_id,
        News.id != news_id
    ).order_by(News.created_at.desc()).limit(4).all()
    # Check poll voted status
    has_voted = False
    if news_item.poll:
        from app.models import PollVote
        user_ip = request.remote_addr
        uid = current_user.id if current_user.is_authenticated else None
        
        q = PollVote.query.filter_by(poll_id=news_item.poll.id)
        if uid:
            has_voted = q.filter_by(user_id=uid).first() is not None
        else:
            has_voted = q.filter_by(ip_address=user_ip).first() is not None

    return render_template('news.html', news=news_item, comments=comments,
                           latest_news=latest_news, related_news=related_news,
                           user_liked=user_liked, user_bookmarked=user_bookmarked,
                           likes_count=likes_count, has_voted=has_voted)

@main.route('/api/news/<int:news_id>/bookmark', methods=['POST'])
def toggle_bookmark(news_id):
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Кіру қажет'}), 401
        
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, news_id=news_id).first()
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'removed'})
    else:
        new_bookmark = Bookmark(user_id=current_user.id, news_id=news_id)
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'added'})

@main.route('/api/news/<int:news_id>/like', methods=['POST'])
def toggle_like(news_id):
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Кіру қажет'}), 401
        
    like = Like.query.filter_by(user_id=current_user.id, news_id=news_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        likes_count = Like.query.filter_by(news_id=news_id).count()
        return jsonify({'status': 'success', 'action': 'removed', 'count': likes_count})
    else:
        new_like = Like(user_id=current_user.id, news_id=news_id)
        db.session.add(new_like)
        db.session.commit()
        likes_count = Like.query.filter_by(news_id=news_id).count()
        return jsonify({'status': 'success', 'action': 'added', 'count': likes_count})

@main.route('/news/<int:news_id>/comment', methods=['POST'])
def add_comment(news_id):
    content = request.form.get('content')
    if not content or not content.strip():
        return redirect(url_for('main.news_detail', news_id=news_id))
        
    new_comment = Comment(
        content=content.strip(),
        news_id=news_id,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    
    if not current_user.is_authenticated:
        new_comment.guest_name = "Аноним"
        
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('main.news_detail', news_id=news_id))

@main.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in ['kk', 'ru', 'en']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('main.index'))

@main.route('/about')
def about():
    return render_template('pages/about.html')

@main.route('/contacts')
def contacts():
    return render_template('pages/contacts.html')

@main.route('/advertising')
def advertising():
    return render_template('pages/advertising.html')

@main.route('/api/news/latest')
def api_latest_news():
    """
    Endpoint for JS polling to get newest articles without reloading
    """
    since_timestamp = request.args.get('since')
    if not since_timestamp:
        return jsonify([])
        
    from datetime import datetime
    try:
        since_dt = datetime.fromisoformat(since_timestamp)
        new_news = News.query.filter(News.created_at > since_dt).order_by(News.created_at.desc()).all()
        return jsonify([n.to_dict() for n in new_news])
    except Exception as e:
        return jsonify([])

@main.route('/api/news/urgent')
def api_urgent_news():
    """
    Returns the most viewed news of the last 48 hours for urgent toast notifications.
    """
    from datetime import datetime, timedelta
    lang = session.get('lang', 'ru')
    
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    urgent_news = News.query.filter(News.created_at >= two_days_ago).order_by(News.views.desc()).first()
    
    if not urgent_news:
        urgent_news = News.query.order_by(News.created_at.desc()).first()
        
    if urgent_news:
        return jsonify({
            'id': urgent_news.id,
            'title': getattr(urgent_news, f'title_{lang}', urgent_news.title_ru),
            'url': url_for('main.news_detail', news_id=urgent_news.id)
        })
    return jsonify(None)

@main.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])
        
    lang = session.get('lang', 'ru')
    title_field = getattr(News, f'title_{lang}')
    
    results = News.query.filter(title_field.ilike(f'%{q}%')).order_by(News.created_at.desc()).limit(5).all()
    
    return jsonify([{
        'id': n.id,
        'title': getattr(n, f'title_{lang}'),
        'date': n.created_at.strftime('%d.%m %H:%M')
    } for n in results])

@main.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        email = email.strip().lower()
        from app.models import Subscriber
        from flask import flash
        
        # Check if already subscribed
        existing = Subscriber.query.filter_by(email=email).first()
        if not existing:
            new_sub = Subscriber(email=email)
            db.session.add(new_sub)
            db.session.commit()
            flash('Сәтті жазылдыңыз! (Вы успешно подписались!)', 'success')
        else:
            flash('Бұл пошта тіркеліп қойған. (Этот email уже зарегистрирован.)', 'info')
            
    return redirect(request.referrer or url_for('main.index'))

@main.route('/tag/<tag_name>')
def tag_news(tag_name):
    from app.models import Tag
    tag = Tag.query.filter_by(name=tag_name.lower()).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    # Get news that have this tag
    pagination = tag.news.order_by(News.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    news_list = pagination.items
    
    return render_template('tag.html', tag=tag, news_list=news_list, pagination=pagination)

@main.route('/api/poll/<int:poll_id>/vote', methods=['POST'])
def poll_vote(poll_id):
    from app.models import Poll, PollOption, PollVote
    poll = Poll.query.get_or_404(poll_id)
    
    user_ip = request.remote_addr
    uid = current_user.id if current_user.is_authenticated else None
    
    # Check if already voted
    q = PollVote.query.filter_by(poll_id=poll.id)
    if uid:
        already_voted = q.filter_by(user_id=uid).first() is not None
    else:
        already_voted = q.filter_by(ip_address=user_ip).first() is not None
        
    if already_voted:
        return jsonify({'status': 'error', 'message': 'Вы уже голосовали'}), 400
        
    option_id = request.form.get('option_id')
    if not option_id:
        return jsonify({'status': 'error', 'message': 'Выберите вариант'}), 400
        
    option = PollOption.query.filter_by(id=option_id, poll_id=poll.id).first()
    if not option:
        return jsonify({'status': 'error', 'message': 'Вариант не найден'}), 404
        
    # Register vote
    option.votes += 1
    new_vote = PollVote(poll_id=poll.id, user_id=uid, ip_address=user_ip)
    db.session.add(new_vote)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@main.route('/api/news/<int:news_id>/tts/<lang>')
def get_news_tts(news_id, lang):
    import os
    import re
    from flask import current_app, send_file
    from gtts import gTTS
    
    news_item = News.query.get_or_404(news_id)
    text = getattr(news_item, f'content_{lang}', None) or getattr(news_item, f'title_{lang}', '')
    
    # Strip HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    if not clean_text.strip():
        clean_text = "Текст отсутствует"
        
    # Setup audio dir
    audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    
    filename = f"news_{news_id}_{lang}.mp3"
    filepath = os.path.join(audio_dir, filename)
    
    if not os.path.exists(filepath):
        try:
            tts = gTTS(text=clean_text, lang=lang)
            tts.save(filepath)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return send_file(filepath, mimetype="audio/mpeg")
