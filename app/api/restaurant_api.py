# /app/api/restaurant_api.py
from . import bp  # 从 app/api/__init__.py 导入 'bp' 蓝图
from app import db
from app.models import Restaurant, MerchantDiscountRule, Order, OrderItem, User, Dish,UserPriceLevel
from flask import request, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy import func
@bp.route('/restaurant/login', methods=['POST'])
def restaurant_login():
    """
    商家登录 API
    (这是一个非常简化的版本，仅用于课程设计演示)
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "缺少用户名或密码"}), 400

    # 在真实项目中，应该查询哈希加密后的密码
    restaurant = Restaurant.query.filter_by(MerchantUsername=username).first()

    if restaurant and restaurant.check_password(password):
        # 登录成功，返回商家信息
        return jsonify({
            "message": "登录成功",
            "restaurant_id": restaurant.RestaurantID,
            "name": restaurant.Name
        }), 200
    else:
        # 登录失败
        return jsonify({"error": "用户名或密码错误"}), 401

@bp.route('/restaurant/<int:restaurant_id>/rules', methods=['GET'])
def get_rules(restaurant_id):
    """
    获取指定餐厅的当前折扣规则
    """
    rules = MerchantDiscountRule.query.filter_by(RestaurantID=restaurant_id).all()

    if not rules:
        # 即使没有规则，也返回一个空列表，而不是 404
        return jsonify([])

    # 将查询结果序列化为 JSON
    output = []
    for rule in rules:
        output.append({
            "PriceLevel": rule.PriceLevel,
            "Discount": rule.Discount
        })
    
    # 按 PriceLevel 排序，使其更易读
    return jsonify(sorted(output, key=lambda x: x['PriceLevel']))

@bp.route('/restaurant/<int:restaurant_id>/rules', methods=['POST'])
def set_rules(restaurant_id):
    """
    (核心功能) 设置或更新一个餐厅的折扣规则
    
    预期传入的 JSON 格式:
    [
        { "PriceLevel": 1, "Discount": 0.9 },
        { "PriceLevel": 2, "Discount": 0.95 },
        ...
        { "PriceLevel": 5, "Discount": 1.1 }
    ]
    """
    data = request.json
    if not isinstance(data, list) or len(data) == 0:
        return jsonify({"error": "无效的输入，需要一个包含规则的 JSON 列表"}), 400

    # 检查餐厅是否存在
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"error": "未找到该餐厅"}), 404

    # --- 事务性更新 ---
    # 我们先删除该商家的所有旧规则，再插入新规则
    # 这是最简单、最幂等（可重复执行）的更新方式
    try:
        # 1. 删除旧规则
        MerchantDiscountRule.query.filter_by(RestaurantID=restaurant_id).delete()

        # 2. 插入新规则
        new_rules = []
        for item in data:
            level = item.get('PriceLevel')
            discount = item.get('Discount')
            
            # (简单的验证)
            if not (isinstance(level, int) and isinstance(discount, (int, float))):
                raise ValueError("规则条目必须包含 PriceLevel (整数) 和 Discount (数字)")

            rule = MerchantDiscountRule(
                RestaurantID=restaurant_id,
                PriceLevel=level,
                Discount=discount
            )
            new_rules.append(rule)
        
        db.session.add_all(new_rules)
        db.session.commit() # 提交事务
        
        return jsonify({
            "message": f"成功为 {restaurant.Name} 更新了 {len(new_rules)} 条规则",
            "new_rules_count": len(new_rules)
        }), 201 # 201 Created or Updated

    except Exception as e:
        db.session.rollback() # 发生错误，回滚
        return jsonify({"error": f"更新失败: {str(e)}"}), 500
    
# /app/api/restaurant_api.py
# ... (在 set_rules 函数之后) ...

@bp.route('/restaurant/register', methods=['POST'])
def restaurant_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    location = data.get('location')

    if not all([username, password, name]):
        return jsonify({"error": "缺少商家用户名、密码或餐厅名称"}), 400

    if Restaurant.query.filter_by(MerchantUsername=username).first():
        return jsonify({"error": "该商家用户名已被注册"}), 400

    try:
        new_restaurant = Restaurant(
            MerchantUsername=username,
            Name=name,
            Location=location
        )
        new_restaurant.set_password(password) # 使用哈希
        
        db.session.add(new_restaurant)
        db.session.commit()

        return jsonify({
            "message": "商家注册成功",
            "restaurant_id": new_restaurant.RestaurantID
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"注册失败: {str(e)}"}), 500
    
@bp.route('/restaurant/<int:restaurant_id>/orders', methods=['GET'])
def get_restaurant_orders(restaurant_id):
    """
    (新) 获取该餐厅的订单
    允许按状态筛选, e.g., /api/restaurant/1/orders?status=Pending
    """
    status_filter = request.args.get('status')
    
    try:
        query = Order.query.filter_by(RestaurantID=restaurant_id)

        if status_filter:
            query = query.filter_by(Status=status_filter)
            
        orders = query.order_by(Order.OrderTime.desc()).limit(50).all()
        
        output = []
        for order in orders:
            user_name = order.User.Username if order.User else "未知用户"
            
            items_output = []
            for item in order.Items:
                items_output.append({
                    "dish_name": item.Dish.Name if item.Dish else "未知菜品",
                    "quantity": item.Quantity,
                    "final_price_per_item": item.FinalPricePerItem
                })
            
            output.append({
                "order_id": order.OrderID,
                "user_name": user_name,
                "status": order.Status,
                "total_price": order.TotalPrice,
                "order_time": order.OrderTime.isoformat(),
                "items": items_output
            })

        return jsonify(output), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/order/<int:order_id>/update_status', methods=['POST'])
def update_order_status(order_id):
    """
    (新) 更新订单状态 (商家用)
    预期 JSON: { "status": "Confirmed" }
    """
    data = request.json
    new_status = data.get('status')

    if not new_status:
        return jsonify({"error": "缺少 'status'"}), 400

    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "订单未找到"}), 404
        
        order.Status = new_status
        db.session.commit()
        
        return jsonify({
            "message": "订单状态更新成功",
            "order_id": order.OrderID,
            "new_status": order.Status
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@bp.route('/restaurant/<int:restaurant_id>/stats', methods=['GET'])
def get_restaurant_stats(restaurant_id):
    """
    (新增) 真实数据接口：为前端 ECharts 提供数据库里的实时统计
    """
    try:
        # 1. 统计热销菜品 (Top 5)
        # SQL逻辑: select Name, sum(Quantity) from OrderItem join Dish group by DishID order by sum desc
        top_dishes_query = db.session.query(
            Dish.Name,
            func.sum(OrderItem.Quantity).label('total_qty')
        ).join(OrderItem, OrderItem.DishID == Dish.DishID)\
         .filter(Dish.RestaurantID == restaurant_id)\
         .group_by(Dish.Name)\
         .order_by(func.sum(OrderItem.Quantity).desc())\
         .limit(5).all()

        # 2. 统计用户等级分布
        # SQL逻辑: select PriceLevel, count(*) from UserPriceLevel where RestaurantID=... group by PriceLevel
        level_dist_query = db.session.query(
            UserPriceLevel.PriceLevel,
            func.count(UserPriceLevel.UserID)
        ).filter_by(RestaurantID=restaurant_id)\
         .group_by(UserPriceLevel.PriceLevel).all()

        # 3. 格式化为前端 ECharts 需要的 JSON
        stats_data = {
            "dishes_names": [r[0] for r in top_dishes_query], # ['红烧肉', '米饭'...]
            "dishes_values": [int(r[1]) for r in top_dishes_query], # [100, 80...]
            "levels_data": [
                {"name": f"Level {r[0]}", "value": r[1]} for r in level_dist_query
            ]
        }
        
        # 如果没有数据（新店开张），给点默认值防止前端报错
        if not stats_data["dishes_names"]:
            stats_data["dishes_names"] = ["暂无数据"]
            stats_data["dishes_values"] = [0]
            
        return jsonify(stats_data), 200

    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({"error": str(e)}), 500