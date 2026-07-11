import hashlib

def hash_file_content(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()


    