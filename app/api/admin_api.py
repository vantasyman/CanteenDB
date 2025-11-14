# /app/api/admin_api.py
from . import bp
from app.tasks import run_ml_pipeline
from flask import jsonify, current_app # <-- 【修改】导入 current_app

@bp.route('/admin/run_kmeans', methods=['POST'])
def run_kmeans_endpoint():
    """
    (演示按钮 API)
    立即触发 K-Means 聚类任务
    """
    print("[API] K-Means run triggered by button.")
    try:
        # 【核心修复】必须在这里为 K-Means 任务提供应用上下文！
        # 我们使用 'current_app.app_context()'
        with current_app.app_context():
            result = run_ml_pipeline()
        
        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500