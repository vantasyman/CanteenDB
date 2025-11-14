# /run.py
from app import create_app
from flask import render_template, redirect, url_for # <-- 额外导入 redirect, url_for

app = create_app()

@app.route('/')
def login_page():
    return render_template('login.html')

# --- 【新增这个路由】 ---
@app.route('/dashboard')
def user_dashboard():
    """
    提供用户主页
    (我们稍后会添加逻辑，检查用户是否真的登录了)
    """
    return render_template('user_dashboard.html')
# --- 【新增结束】 ---
@app.route('/merchant_dashboard')
def merchant_dashboard():
    """
    提供商家管理后台页面
    (TODO: 这里未来要加登录检查)
    """
    return render_template('merchant_dashboard.html')
if __name__ == '__main__':
    app.run(debug=True)