# /app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config,instance_path

# 1. 初始化 SQLAlchemy 实例 (但不绑定 app)
db = SQLAlchemy()

def create_app(config_class=Config):
    """
    应用工厂函数
    """
    app = Flask(__name__, instance_path=instance_path)
    
    # 2. 从 config.py 加载配置
    app.config.from_object(config_class)
    
    # 3. 将 db 实例与 app 绑定
    db.init_app(app)
    
    # 4. (关键) 导入我们的模型
    #    我们在这里导入，以防止循环导入
    with app.app_context():
        from . import models
        db.create_all() # 自动创建所有不存在的表
    
    # 5. (稍后) 在这里注册我们的 API 蓝图
    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/hello')
    def hello():
        return "Hello, Canteen App is running!"

    return app