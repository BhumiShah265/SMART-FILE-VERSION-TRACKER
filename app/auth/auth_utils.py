from werkzeug.security import generate_password_hash, check_password_hash
def generate_password(password):
    return generate_password_hash(password)

def check_password(stored_hash,password):
    return check_password_hash(stored_hash, password)