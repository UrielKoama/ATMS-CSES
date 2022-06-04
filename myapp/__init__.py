import os

from flask import Flask
from flask_sqlalchemy import  SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_datepicker import datepicker
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from os import environ
import pymysql
from flask import jsonify

con = SQLAlchemy()
migrate = Migrate()
DB_CSES = "database.db"

# def gen_connection_string():
#     # if not on Google then use local MySQL
#     if not os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
#         return 'mysql://root@localhost/blog'
#     else:
#         conn_name = os.environ.get('CLOUDSQL_CONNECTION_NAME' '')
#         sql_user = os.environ.get('CLOUDSQL_USER', 'root')
#         sql_pass = os.environ.get('CLOUDSQL_PASSWORD', '')
#         conn_template = 'mysql+mysqldb://%s:%s@/blog?unix_socket=/cloudsql/%s'
#         return conn_template % (sql_user, sql_pass, conn_name)

def create():
    app = Flask(__name__)
    CKEditor(app)
    datepicker(app)
    Bootstrap(app)
    migrate.init_app(app,con)
    app.config['SECRET_KEY'] = '6f92d930a02eb8ee92e1ae34a0c31d6c'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = gen_connection_string()
    #environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    # or  f'sqlite:///{DB_CSES}'

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
