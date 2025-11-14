# /app/api/order_api.py
from . import bp
from app import db
from app.models import (
    UserPriceLevel, MerchantDiscountRule, Dish, Order, OrderItem, UserBehaviorLog
)
from flask import request, jsonify
from datetime import datetime

@bp.route('/log/behavior', methods=['POST'])
def log_behavior():
    """
    (闭环输入) 记录用户行为
    """
    data = request.json
    try:
        log = UserBehaviorLog(
            UserID=data.get('user_id'),
            RestaurantID=data.get('restaurant_id'),
            ActionType=data.get('action_type'),
            Timestamp=datetime.now()
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({"message": "Log received"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Log failed: {str(e)}"}), 500

@bp.route('/order/create', methods=['POST'])
def create_order():
    """
    (核心 API) 创建订单，并实时计算“个性化定价”
    """
    data = request.json
    user_id = data.get('user_id')
    restaurant_id = data.get('restaurant_id')
    dish_ids = data.get('dish_ids')

    if not all([user_id, restaurant_id, dish_ids]):
        return jsonify({"error": "缺少 user_id, restaurant_id 或 dish_ids"}), 400

    try:
        # --- 1. 获取用户的“价格等级”(ML 的输出) ---
        user_level_entry = UserPriceLevel.query.get({
            'UserID': user_id, 
            'RestaurantID': restaurant_id
        })
        price_level = user_level_entry.PriceLevel if user_level_entry else 1
        print(f"[Order] UserID {user_id} @ RestID {restaurant_id} -> PriceLevel: {price_level}")

        # --- 2. 获取商家的“折扣规则”(业务规则) ---
        discount_rule = MerchantDiscountRule.query.get({
            'RestaurantID': restaurant_id, 
            'PriceLevel': price_level
        })
        discount = discount_rule.Discount if discount_rule else 1.0
        print(f"[Order] PriceLevel {price_level} -> Discount: {discount}")

        # --- 3. 计算价格并准备订单详情 ---
        order_total_price = 0
        order_items_to_create = []
        dish_counts = {}
        for dish_id in dish_ids:
            dish_counts[dish_id] = dish_counts.get(dish_id, 0) + 1

        dishes_in_db = Dish.query.filter(Dish.DishID.in_(dish_counts.keys())).all()
        dish_price_map = {d.DishID: d.BasePrice for d in dishes_in_db}

        for dish_id, quantity in dish_counts.items():
            base_price = dish_price_map.get(dish_id)
            if base_price is None:
                raise ValueError(f"菜品 ID {dish_id} 未找到")

            final_price_per_item = base_price * discount
            order_items_to_create.append(OrderItem(
                DishID=dish_id,
                Quantity=quantity,
                FinalPricePerItem=final_price_per_item
            ))
            order_total_price += final_price_per_item * quantity

        # --- 4. 创建主订单 (状态为 Pending) ---
        new_order = Order(
            UserID=user_id,
            RestaurantID=restaurant_id,
            Status='Pending', # (关键) 状态为“待处理”, 供商家确认
            TotalPrice=order_total_price,
            OrderTime=datetime.now(),
            Items=order_items_to_create
        )
        db.session.add(new_order)

        # --- 5. (闭环完成) 将“下单”行为写回日志 ---
        order_log = UserBehaviorLog(
            UserID=user_id,
            RestaurantID=restaurant_id,
            ActionType='order_placed',
            Timestamp=datetime.now()
        )
        db.session.add(order_log)
        
        # --- 6. 提交事务 ---
        db.session.commit()

        print(f"[Order] 成功创建订单 {new_order.OrderID}, 总价: {order_total_price}")

        # --- 7. 返回“个性化”结果 ---
        return jsonify({
            "message": "下单成功!",
            "order_id": new_order.OrderID,
            "total_price": new_order.TotalPrice,
            "price_level_used": price_level,
            "discount_applied": discount
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Order] 失败: {str(e)}")
        return jsonify({"error": f"下单失败: {str(e)}"}), 500