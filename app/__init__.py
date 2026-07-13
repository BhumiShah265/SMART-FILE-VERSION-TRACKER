import os
from flask import Flask
from app.database.db import db
from app.routes.auth_routes import auth_bp
from app.routes.main_routes import main_bp
from app.routes.file_routes import file_bp
from dotenv import load_dotenv
import os
from app.backup.scheduler import start_scheduler
start_scheduler()
load_dotenv()
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'somerandomhere'
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(file_bp)

    with app.app_context():
        from app.database import models

    return app