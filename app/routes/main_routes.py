from flask import Blueprint,render_template, redirect,url_for, session
from app.database.models import File
from flask import request
main_bp = Blueprint('main',__name__)
@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))


@main_bp.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    search_query = request.args.get('q','')
    if search_query:
        files = File.query.filter_by(owner_id = session['user_id']).filter(File.file_name.contains(search_query)).all()
    else:
        files = File.query.filter_by(owner_id =session['user_id']).all()
    
    return render_template('dashboard.html', files = files, search_query = search_query)
