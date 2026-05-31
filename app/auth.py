from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Bookmark, Like, News
from app import db
from datetime import datetime
try:
    from authlib.integrations.flask_client import OAuth
    oauth_enabled = True
except ImportError:
    oauth_enabled = False

auth_bp = Blueprint('auth', __name__)
oauth = None

def init_oauth(app):
    global oauth
    if oauth_enabled:
        oauth = OAuth(app)
        
        # We check if client keys are present
        google_client_id = app.config.get('GOOGLE_CLIENT_ID')
        google_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
        
        if google_client_id and google_client_secret:
            oauth.register(
                name='google',
                client_id=google_client_id,
                client_secret=google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )

        fb_client_id = app.config.get('FACEBOOK_CLIENT_ID')
        fb_client_secret = app.config.get('FACEBOOK_CLIENT_SECRET')
        if fb_client_id and fb_client_secret:
            oauth.register(
                name='facebook',
                client_id=fb_client_id,
                client_secret=fb_client_secret,
                api_base_url='https://graph.facebook.com/v15.0/',
                access_token_url='https://graph.facebook.com/v15.0/oauth/access_token',
                authorize_url='https://www.facebook.com/v15.0/dialog/oauth',
                client_kwargs={'scope': 'email public_profile'}
            )

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Бұл логин бос емес', 'error')
            return redirect(url_for('auth.register'))
        if email and User.query.filter_by(email=email).first():
            flash('Бұл email тіркелген', 'error')
            return redirect(url_for('auth.register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.index'))
        
    return render_template('auth/register.html', oauth_enabled=oauth_enabled)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Қате логин немесе пароль', 'error')
            
    return render_template('auth/login.html', oauth_enabled=oauth_enabled)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    likes = Like.query.filter_by(user_id=current_user.id).order_by(Like.created_at.desc()).all()
    return render_template('auth/profile.html', bookmarks=bookmarks, likes=likes)

# OAuth Routes
@auth_bp.route('/login/<provider>')
def login_oauth(provider):
    if not oauth_enabled or not oauth or not hasattr(oauth, provider):
        flash('Бұл жүйе әзірше бапталмаған.', 'error')
        return redirect(url_for('auth.login'))
    
    redirect_uri = url_for('auth.authorize_oauth', provider=provider, _external=True)
    return getattr(oauth, provider).authorize_redirect(redirect_uri)

@auth_bp.route('/authorize/<provider>')
def authorize_oauth(provider):
    if not oauth_enabled or not oauth or not hasattr(oauth, provider):
        return redirect(url_for('auth.login'))
        
    token = getattr(oauth, provider).authorize_access_token()
    if provider == 'google':
        user_info = token.get('userinfo')
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('sub')
        avatar = user_info.get('picture')
        
        user = User.query.filter_by(google_id=google_id).first()
        if not user and email:
            user = User.query.filter_by(email=email).first()
        
        if not user:
            user = User(username=name, email=email, google_id=google_id, avatar_url=avatar)
            db.session.add(user)
            db.session.commit()
        else:
            user.google_id = google_id
            user.avatar_url = avatar
            db.session.commit()
            
        login_user(user)
        
    elif provider == 'facebook':
        # Need to fetch user profile for facebook
        resp = oauth.facebook.get('me?fields=id,name,email,picture')
        user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        fb_id = user_info.get('id')
        avatar = ''
        if 'picture' in user_info and 'data' in user_info['picture']:
            avatar = user_info['picture']['data'].get('url', '')
            
        user = User.query.filter_by(facebook_id=fb_id).first()
        if not user and email:
            user = User.query.filter_by(email=email).first()
            
        if not user:
            user = User(username=name, email=email, facebook_id=fb_id, avatar_url=avatar)
            db.session.add(user)
            db.session.commit()
        else:
            user.facebook_id = fb_id
            if avatar: user.avatar_url = avatar
            db.session.commit()
            
        login_user(user)

    return redirect(url_for('main.index'))
