# /app/api/user_api.py
from . import bp
from app import db
from app.models import User, Restaurant, Dish, UserPriceLevel, MerchantDiscountRule
from flask import request, jsonify

@bp.route('/user/login', methods=['POST'])
def user_login():
    """
    用户登录 API
    (同样是简化版)
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "缺少用户名或密码"}), 400

    user = User.query.filter_by(Username=username).first()
    if user and user.check_password(password):
        return jsonify({
            "message": "登录成功",
            "user_id": user.UserID,
            "username": user.Username
        }), 200
    else:
        # 登录失败
        return jsonify({"error": "用户名或密码错误"}), 401

@bp.route('/restaurants', methods=['GET'])
def get_all_restaurants():
    """
    (页面核心) 获取所有餐厅列表
    """
    try:
        restaurants = Restaurant.query.all()
        output = []
        for r in restaurants:
            output.append({
                "id": r.RestaurantID,
                "name": r.Name,
                "location": r.Location
            })
        return jsonify(output), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/restaurant/<int:restaurant_id>/dishes', methods=['GET'])
def get_dishes_for_restaurant(restaurant_id):
    """
    (核心 API - 已重构) 
    获取指定餐厅的菜品, 并为指定用户实时计算“个性化价格”
    
    预期请求: GET /api/restaurant/1/dishes?user_id=1
    """
    
    # --- 1. 获取 UserID ---
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "缺少 'user_id' 参数"}), 400
    
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "'user_id' 必须是整数"}), 400

    try:
        # --- 2. 获取用户的“价格等级”(ML 的输出) ---
        user_level_entry = UserPriceLevel.query.get({
            'UserID': user_id, 
            'RestaurantID': restaurant_id
        })
        
        # 默认为 1 级 (新用户或低价值用户)
        price_level = user_level_entry.PriceLevel if user_level_entry else 1
        print(f"[API GetDishes] UserID {user_id} @ RestID {restaurant_id} -> PriceLevel: {price_level}")

        # --- 3. 获取商家的“折扣规则”(业务规则) ---
        discount_rule = MerchantDiscountRule.query.get({
            'RestaurantID': restaurant_id, 
            'PriceLevel': price_level
        })
        
        # 默认折扣为 1.0 (原价)
        discount = discount_rule.Discount if discount_rule else 1.0
        # (生成您要的 "98%" "110%" 标签)
        discount_label = f"{int(discount * 100)}%"
        print(f"[API GetDishes] PriceLevel {price_level} -> Discount: {discount} (Label: {discount_label})")
        
        # --- 4. 获取所有菜品, 并实时计算价格 ---
        dishes = Dish.query.filter_by(RestaurantID=restaurant_id).all()
        
        output = []
        for d in dishes:
            # !!! 核心逻辑 !!!
            base_price = d.BasePrice
            final_price = base_price * discount

            output.append({
                "id": d.DishID,
                "name": d.Name,
                "image_url": d.image_url,         # (新) 返回图片 URL
                "base_price": base_price,         # (新) 返回原价
                "final_price": final_price,       # (新) 返回最终价
                "discount_label": discount_label  # (新) 返回 "98%" 标签
            })
        
        return jsonify(output), 200

    except Exception as e:
        print(f"[API GetDishes] Error: {str(e)}")
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500
    
@bp.route('/user/register', methods=['POST'])
def user_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    area = data.get('area')

    if not all([username, password]):
        return jsonify({"error": "缺少用户名或密码"}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(Username=username).first():
        return jsonify({"error": "该用户名已被注册"}), 400

    # 创建新用户
    try:
        new_user = User(Username=username, Area=area)
        new_user.set_password(password) # 使用哈希
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "message": "用户注册成功",
            "user_id": new_user.UserID
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"注册失败: {str(e)}"}), 500