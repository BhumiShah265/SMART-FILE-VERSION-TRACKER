import os
from flask import Blueprint, request, redirect, url_for, session, render_template
from app.database.db import db
from app.database.models import File, Version,Folder
from app.core.hashing import hash_file_content
from app.core.diffing import get_diff
from app.compression.compressor import compress_file, decompress_file
file_bp = Blueprint('file',__name__)
from app.backup.scheduler import backup_storage

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
            new_storage_path = f"{folder_path}/v{new_version_number}_{uploaded_file.filename}.zip"

            compress_file(file_bytes,new_storage_path,arcname= uploaded_file.filename)

            new_version = Version(
                file_id = existing_file.id,
                version_number = new_version_number,
                storage_path = new_storage_path,
                hash = file_hash
            )
            db.session.add(new_version)
            db.session.commit()

            return redirect(url_for('main.dashboard'))
    
        else:
            new_file = File(
                file_name = uploaded_file.filename,
                owner_id = session['user_id'],
                folder_id = folder_id
            )
            db.session.add(new_file)
            db.session.commit()

            folder_path = f"storage/user_{session['user_id']}/file_{new_file.id}"
            os.makedirs(folder_path, exist_ok=True)
            storage_path = f"{folder_path}/v1_{uploaded_file.filename}.zip"

            compress_file(file_bytes, storage_path, arcname=uploaded_file.filename)

            new_version = Version(
                file_id = new_file.id,
                version_number = 1,
                storage_path = storage_path,
                hash = file_hash
            )
            db.session.add(new_version)
            db.session.commit()

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
    file_obj = File.query.get(file_id)  

    content_1_bytes = decompress_file(version_1.storage_path, file_obj.file_name)
    content_2_bytes = decompress_file(version_2.storage_path, file_obj.file_name)

    content_1 = content_1_bytes.decode('utf-8')
    content_2 = content_2_bytes.decode('utf-8')
    diff_lines = get_diff(content_1,content_2)
    file = File.query.get(file_id)
    versions = Version.query.filter_by(file_id=file_id).order_by(Version.version_number).all()
    return render_template('history.html',file = file, versions = versions,diff_lines=diff_lines)

@file_bp.route('/restore/<int:version_id>')
def restore_version(version_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    old_version = Version.query.get(version_id)
    file_obj = File.query.get(old_version.file_id)

    file_bytes = decompress_file(old_version.storage_path, file_obj.file_name)

    latest_version = Version.query.filter_by(file_id=old_version.file_id).order_by(Version.version_number.desc()).first()
    new_version_number = latest_version.version_number + 1

    folder_path = f"storage/user_{session['user_id']}/file_{old_version.file_id}"
    new_storage_path = f"{folder_path}/v{new_version_number}_restored.zip"

    compress_file(file_bytes, new_storage_path, arcname=file_obj.file_name)

    new_version = Version(
        file_id=old_version.file_id,
        version_number=new_version_number,
        storage_path=new_storage_path,
        hash=old_version.hash
    )
    db.session.add(new_version)
    db.session.commit()

    return redirect(url_for('file.view_history', file_id=old_version.file_id))

@file_bp.route('/backup-now')
def backup_now():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    backup_storage()
    return redirect(url_for('main.dashboard'))
