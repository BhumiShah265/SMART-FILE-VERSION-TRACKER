import os
import zlib
import hashlib
import difflib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cinematic-vault-key-99'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///version_control.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class FileRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    versions = db.relationship('FileVersion', backref='file_record', lazy=True)

class FileVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_record.id'))
    version_number = db.Column(db.Integer)
    hash_val = db.Column(db.String(64))
    compressed_data = db.Column(db.LargeBinary)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Helper Functions ---
def compress_file(data):
    return zlib.compress(data)

def decompress_file(data):
    return zlib.decompress(data)

def get_file_hash(data):
    return hashlib.sha256(data).hexdigest()

# --- Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    un = request.form.get('username')
    pw = request.form.get('password')
    if User.query.filter_by(username=un).first():
        flash('User already exists')
        return redirect(url_for('index'))
    new_user = User(username=un, password=generate_password_hash(pw))
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    un = request.form.get('username')
    pw = request.form.get('password')
    user = User.query.filter_by(username=un).first()
    if user and check_password_hash(user.password, pw):
        login_user(user)
        return redirect(url_for('dashboard'))
    flash('Invalid credentials')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    files = FileRecord.query.filter_by(user_id=current_user.id).all()
    
    # Calculate Stats for the "Cinematic" UI
    all_versions = FileVersion.query.join(FileRecord).filter(FileRecord.user_id == current_user.id).all()
    total_versions = len(all_versions)
    
    compressed_size_bytes = sum(len(v.compressed_data) for v in all_versions)
    compressed_size_kb = round(compressed_size_bytes / 1024, 1)
    
    # Raw size estimation (approx 40% more than compressed for text)
    raw_size_kb = round(compressed_size_kb * 1.4, 1)

    return render_template('dashboard.html', 
                           files=files, 
                           total_files=len(files), 
                           total_v=total_versions,
                           raw_size=raw_size_kb,
                           comp_size=compressed_size_kb)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files: return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '': return redirect(url_for('dashboard'))
    
    content = file.read()
    file_hash = get_file_hash(content)
    
    record = FileRecord.query.filter_by(filename=file.filename, user_id=current_user.id).first()
    if not record:
        record = FileRecord(filename=file.filename, user_id=current_user.id)
        db.session.add(record)
        db.session.commit()
    
    last_version = FileVersion.query.filter_by(file_id=record.id).order_by(FileVersion.version_number.desc()).first()
    
    if last_version and last_version.hash_val == file_hash:
        flash("No changes detected.")
    else:
        new_v_num = (last_version.version_number + 1) if last_version else 1
        new_v = FileVersion(
            file_id=record.id,
            version_number=new_v_num,
            hash_val=file_hash,
            compressed_data=compress_file(content)
        )
        db.session.add(new_v)
        db.session.commit()
        flash(f"Version {new_v_num} Synced.")
        
    return redirect(url_for('dashboard'))

@app.route('/download/<int:version_id>')
@login_required
def download_version(version_id):
    version = FileVersion.query.get_or_404(version_id)
    record = FileRecord.query.get(version.file_id)
    if record.user_id != current_user.id: return "Unauthorized", 403
    
    data = decompress_file(version.compressed_data)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"dl_{record.filename}")
    with open(temp_path, 'wb') as f:
        f.write(data)
    
    return send_file(temp_path, as_attachment=True, download_name=record.filename)
@app.route('/archive')
@login_required
def archive():
    # Gets all versions across all files, sorted by newest first
    all_versions = FileVersion.query.join(FileRecord).filter(
        FileRecord.user_id == current_user.id
    ).order_by(FileVersion.timestamp.desc()).all()
    
    return render_template('archives.html', versions=all_versions)

@app.route('/restore/<int:version_id>')
@login_required
def restore_version(version_id):
    old_version = FileVersion.query.get_or_404(version_id)
    record = FileRecord.query.get(old_version.file_id)
    
    if record.user_id != current_user.id:
        return "Unauthorized", 403

    # Create a new version entry using the old version's data
    last_v = FileVersion.query.filter_by(file_id=record.id).order_by(FileVersion.version_number.desc()).first()
    
    restored_v = FileVersion(
        file_id=record.id,
        version_number=last_v.version_number + 1,
        hash_val=old_version.hash_val,
        compressed_data=old_version.compressed_data
    )
    db.session.add(restored_v)
    db.session.commit()
    flash(f"Restored {record.filename} to Version {old_version.version_number}")
    return redirect(url_for('dashboard'))

@app.route('/diff/<int:v1_id>/<int:v2_id>')
@login_required
def view_diff(v1_id, v2_id):
    v1 = FileVersion.query.get_or_404(v1_id)
    v2 = FileVersion.query.get_or_404(v2_id)
    
    # Check ownership
    if v1.file_record.user_id != current_user.id: return "Forbidden", 403
    
    # Try to decode data to text for comparison
    try:
        text1 = decompress_file(v1.compressed_data).decode('utf-8').splitlines()
        text2 = decompress_file(v2.compressed_data).decode('utf-8').splitlines()
        diff = difflib.HtmlDiff().make_table(text1, text2, fromdesc=f"V{v1.version_number}", todesc=f"V{v2.version_number}")
    except:
        diff = "<div class='p-10 text-center text-slate-500'>Binary file detected. Cannot show text difference.</div>"
        
    return render_template('diff.html', diff_table=diff)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=3000)