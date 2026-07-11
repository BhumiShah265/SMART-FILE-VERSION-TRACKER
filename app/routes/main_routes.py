from flask import Blueprint,render_template, redirect,url_for, session
from app.database.models import File
main_bp = Blueprint('main',__name__)
@main_bp.route('/dashboard')
def dashboard():
    if 'user_id'not in session:
        return redirect(url_for('auth.login'))
    else:
        files = File.query.filter_by(owner_id = session['user_id']).all()
    return render_template('dashboard.html',files=files)

@main_bp.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('auth.login'))