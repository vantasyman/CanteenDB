# /scripts/cluster_script.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.tasks import run_ml_pipeline # 导入纯净的函数

app = create_app()

if __name__ == '__main__':
    print("Running K-Means pipeline from script...")
    
    # 【检查】确保这行 'with app.app_context():' 存在！
    with app.app_context():
        result = run_ml_pipeline()
        
    print(result)