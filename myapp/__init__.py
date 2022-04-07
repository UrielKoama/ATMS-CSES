from flask import Flask
from flask_sqlalchemy import  SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_datepicker import datepicker
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from os import environ

con = SQLAlchemy()
DB_CSES = "database.db"
def create():
    app = Flask(__name__)
    CKEditor(app)
    datepicker(app)
    Bootstrap(app)
    migrate = Migrate(app, con)
    app.config['SECRET_KEY'] = '6f92d930a02eb8ee92e1ae34a0c31d6c'
    app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') # or  f'sqlite:///{DB_CSES}'

    con.init_app(app)

    from .views import view
    from .authentication import auth

    app.register_blueprint(view, url_prefix='/')
    app.register_blueprint(auth, url_prefix = '/auth')

    from .models import User

    create_database(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id): #tell flask what user we are looking for
        return User.query.get(int(id))
    return app

def create_database(app):
    if not path.exists('ATMS-CSES/' + DB_CSES):
        con.create_all(app=app) #tells flask which myapp it creates db for
        print('Created Database!')
