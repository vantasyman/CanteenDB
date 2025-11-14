# /config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(instance_path, 'canteen.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False