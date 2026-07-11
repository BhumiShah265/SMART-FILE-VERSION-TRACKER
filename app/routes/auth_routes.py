from flask import Blueprint, request, render_template, redirect, url_for
from app.database.db import db
from app.database.models import User
from app.auth.auth_utils import generate_password, check_password
from flask import session


auth_bp = Blueprint('auth',__name__)

@auth_bp.route('/signup', methods = ['GET',"POST"])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        number = request.form.get('number')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            return "Wrong input"

        hashed_pw = generate_password(password)

        new_user = User(
            name = name,
            email = email,
            number = number,
            password = hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/login', methods = ['GET','POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email= email).first()
        if user and check_password(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('main.dashboard'))
        else:
            return "Invalid email or password"
    return render_template('login.html')
