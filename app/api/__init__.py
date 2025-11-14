# /app/api/__init__.py
from flask import Blueprint

# 1. 定义一个名为 'api' 的蓝图
#    我们稍后会把所有的 API 路由都注册到这个蓝图上
bp = Blueprint('api', __name__)

# 2. 导入我们的 API 路由模块
#    (注意：这个导入必须放在 'bp' 定义之后，以防止循环导入)
#    我们马上就会去创建 restaurant_api.py
from . import restaurant_api
from . import user_api # <-- 【新增这行导入】
from . import admin_api
from . import order_api