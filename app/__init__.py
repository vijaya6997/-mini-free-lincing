import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .jobs import jobs as jobs_blueprint
    app.register_blueprint(jobs_blueprint, url_prefix='/jobs')

    from .messages import messages as messages_blueprint
    app.register_blueprint(messages_blueprint, url_prefix='/messages')

    from .ratings import ratings as ratings_blueprint
    app.register_blueprint(ratings_blueprint, url_prefix='/ratings')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Create tables
    with app.app_context():
        db.create_all()

    return app
