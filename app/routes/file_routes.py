import os
from flask import Blueprint, request, redirect, url_for, session, render_template
from app.database.db import db
from app.database.models import File, Version
from app.core.hashing import hash_file_content

file_bp = Blueprint('file',__name__)
@file_bp.route('/upload', methods = ['GET','POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        uploaded_file = request.files['file']
        file_bytes = uploaded_file.read()
        file_hash = hash_file_content(file_bytes)

        new_file = File(
            file_name = uploaded_file.filename,
            owner_id = session['user_id']
        )
        db.session.add(new_file)
        db.session.commit()

        folder_path = f"storage/user_{session['user_id']}/file_{new_file.id}"
        os.makedirs(folder_path, exist_ok=True)
        storage_path = f"{folder_path}/v1_{uploaded_file.filename}"

        with open(storage_path, 'wb') as f:
            f.write(file_bytes)

        new_version = Version(
            file_id = new_file.id,
            version_number = 1,
            storage_path = storage_path,
            hash = file_hash
        )
        db.session.add(new_version)
        db.session.commit()

        return redirect(url_for('main.dashboard'))
    return render_template('upload.html')