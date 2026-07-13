import os
from flask import Blueprint, request, redirect, url_for, session, render_template
from app.database.db import db
from app.database.models import File, Version,Folder
from app.core.hashing import hash_file_content
from app.core.diffing import get_diff

file_bp = Blueprint('file',__name__)

@file_bp.route('/upload', methods = ['GET','POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        uploaded_file = request.files['file']
        folder_id = request.form.get('folder_id')
        file_bytes = uploaded_file.read()
        file_hash = hash_file_content(file_bytes)

        existing_file = File.query.filter_by(
            file_name = uploaded_file.filename,
            folder_id = folder_id,
            owner_id = session['user_id']
        ).first()
        if existing_file:
            latest_version = Version.query.filter_by(file_id=existing_file.id).order_by(Version.version_number.desc()).first()
            new_version_number = latest_version.version_number + 1

            folder_path = f"storage/user_{session['user_id']}/file_{existing_file.id}"
            os.makedirs(folder_path, exist_ok=True)
            new_storage_path = f"{folder_path}/v{new_version_number}_{uploaded_file.filename}"

            with open(new_storage_path, 'wb') as f:
                f.write(file_bytes)

            new_version = Version(
                file_id = existing_file.id,
                version_number = new_version_number,
                storage_path = new_storage_path,
                hash = file_hash
            )
            db.session.add(new_version)
            db.session.commit()

            return redirect(url_for('main.dashboard'))
        return redirect(url_for('main.dashboard'))
    folders = Folder.query.filter_by(owner_id = session['user_id']).all()
    return render_template('upload.html',folders=folders)

@file_bp.route('/create_folder', methods = ['GET','POST'])
def create_folder():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        folder_name = request.form.get("name")
        new_folder = Folder(
            name = folder_name,
            owner_id = session['user_id']
        )
        db.session.add(new_folder)
        db.session.commit()

        return redirect(url_for('main.dashboard'))
    return render_template('create_folder.html')

@file_bp.route('/history/<int:file_id>')
def view_history(file_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    file = File.query.get(file_id)
    versions = Version.query.filter_by(file_id=file_id).order_by(Version.version_number).all()
    
    return render_template('history.html',file=file,versions=versions)

@file_bp.route('/compare/<int:file_id>')
def compare_versions(file_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    version_ids = request.args.getlist('v')
    if len(version_ids) != 2:
        return redirect(url_for('file.view_history', file_id = file_id))
    version_1 = Version.query.get(version_ids[0])
    version_2 = Version.query.get(version_ids[1])
    with open(version_1.storage_path,'r') as f:
        content_1 = f.read()

    with open(version_2.storage_path,'r') as f:
        content_2 = f.read()
    diff_lines = get_diff(content_1,content_2)
    file = File.query.get(file_id)
    versions = Version.query.filter_by(file_id=file_id).order_by(Version.version_number).all()
    return render_template('history.html',file = file, versions = versions,diff_lines=diff_lines)

@file_bp.route('/restore/<int:version_id>')
def restore_version(version_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    old_version = Version.query.get(version_id)
    with open(old_version.storage_path,'rb') as f:
        file_bytes = f.read()
    latest_version = Version.query.filter_by(file_id = old_version.file_id).order_by(Version.version_number.desc()).first()
    new_version_number = latest_version.version_number + 1
    folder_path = f"storage/user_{session['user_id']}/file_{old_version.file_id}"
    new_storage_path = f"{folder_path}/v{new_version_number}_restored"

    with open(new_storage_path,'wb') as f:
        f.write(file_bytes)

    new_version = Version(
        file_id = old_version.file_id,
        version_number = new_version_number,
        storage_path= new_storage_path,
        hash = old_version.hash
    )
    db.session.add(new_version)
    db.session.commit()
    return redirect(url_for('file.view_history', file_id = old_version.file_id))
