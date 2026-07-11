from flask import Blueprint,render_template, redirect,url_for, session
main_bp = Blueprint('main',__name__)
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth_login'))
    return render_template('dashboard.html')

@main_bp.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('auth.login'))