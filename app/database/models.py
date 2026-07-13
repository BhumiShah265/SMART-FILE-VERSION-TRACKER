from .db import db
from datetime import datetime,timedelta,timezone

IST = timezone(timedelta(hours=5, minutes =30))
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50),nullable = False)
    email = db.Column(db.String(50),nullable = False, unique = True)
    number = db.Column(db.String(10),nullable = False, unique = True)
    password = db.Column(db.String(200), nullable = False)

class File(db.Model):
    __tablename__ = "file"
    id = db.Column(db.Integer, primary_key = True)
    file_name = db.Column(db.String(100),nullable = False)
    owner_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'),nullable =False)

    @property
    def version_count(self):
        return Version.query.filter_by(file_id = self.id).count()
class Version(db.Model):
    __tablename__ = "version"
    __table_args__ = (db.UniqueConstraint('file_id','version_number',name = 'unique_file_version'),)
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'),nullable = False)
    version_number = db.Column(db.Integer)
    storage_path = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    hash = db.Column(db.String(64))

class Folder(db.Model):
    __tablename__ = "folder"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))

