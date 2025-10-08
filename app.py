import os
from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from config import Config
from models import db, User

app = Flask(__name__)
app.config.from_object(Config)

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(role='admin').first()
        if not admin:
            default_admin = User(
                username='Admin',
                email='admin@elesson.com',
                password=generate_password_hash('admin123'),
                role='admin',
                is_approved=True
            )
            db.session.add(default_admin)
            db.session.commit()
            print("✅ Default admin created (email: admin@elesson.com, password: admin123)")

    app.run(debug=True)
