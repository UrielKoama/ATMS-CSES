from flask import Blueprint,render_template,request,flash,redirect, url_for
from .models import User
from werkzeug.security import check_password_hash, generate_password_hash
from . import con
from .forms import RegistrationForm, LoginForm
from flask_login import login_user,login_required,logout_user,current_user

#has login authentication
auth = Blueprint('auth', __name__)

def add_admin():
    pw = generate_password_hash("Leader22", method='sha256') #need to change from plaintext
    admin_user = User(username='CSES', email="success@msmary.edu", password=pw)
    con.session.add(admin_user)
    con.session.commit()

#Leader22
@auth.route('/login',methods=['GET','POST'])
def login():
    admin_user = User.query.filter_by(email="success@msmary.edu").first()
    if admin_user:
        pass
    else:
        add_admin()
    if current_user.is_authenticated:
        return redirect(url_for('view.calendar'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully! Welcome', category='success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('view.calendar'))
        else:
            flash('Login Unsuccessful Please check email and password.', category='danger')
    return render_template("login.html", user=current_user, title='Login', form=form)

@auth.route('/logout') #decorator
@login_required
def logout():
    logout_user()
    flash("Logged out!")
    return redirect(url_for('auth.login'))

@auth.route('/unauthorized', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.is_authenticated:
        return redirect(url_for('view.home'))
    form= RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        user = User(username= form.username.data,email=form.email.data, password=hashed_password)
        con.session.add(user)
        con.session.commit()
        flash('Account created!', category='success')
        return redirect(url_for('view.home'))
    return render_template('register.html', title='Register', user=current_user, form=form)


