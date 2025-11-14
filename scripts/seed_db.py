import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import User, Restaurant, Dish, UserBehaviorLog, MerchantDiscountRule, UserPriceLevel, Order, OrderItem
from datetime import datetime
from app import create_app , db
app = create_app()
def seed_data():
    """
    清空并填充演示数据
    """
    with app.app_context():
        # --- 1. 清空所有表 (确保幂等性) ---
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # --- 2. 创建用户 (User) ---
        user_alice = User(Username='alice', Area='学生A区')
        user_alice.set_password('password123') # 【修改】调用哈希方法
        
        user_bob = User(Username='bob', Area='学生B区')
        user_bob.set_password('password123')
        
        user_charlie = User(Username='charlie', Area='学生C区')
        user_charlie.set_password('password123')
        
        user_david = User(Username='david', Area='学生A区')
        user_david.set_password('password123')
        
        user_eve = User(Username='eve', Area='学生B区')
        user_eve.set_password('password123')    # 新增用户
        db.session.add_all([user_alice, user_bob, user_charlie, user_david, user_eve]) # 添加他们
        db.session.commit()
        print("Created 5 Users.")
        print(f"Created User: {user_alice.Username} (ID: {user_alice.UserID})")
        print(f"Created User: {user_bob.Username} (ID: {user_bob.UserID})")

        # --- 3. 创建餐厅 (Restaurant) ---
        rest_1 = Restaurant(
            MerchantUsername='merchant_a', 
            Name='第一食堂 (A餐厅)', 
            Location='校园中心',
            image_url='https://placehold.co/400x200/007bff/white?text=第一食堂'
        ) # 【修改】不再传入 password
        rest_1.set_password('pass') # 【修改】调用哈希方法

        rest_2 = Restaurant(
            MerchantUsername='merchant_b',
            Name='风味餐厅 (B餐厅)', 
            Location='西门',
            image_url='https://placehold.co/400x200/28a745/white?text=风味餐厅'
        )
        
        rest_2.set_password('pass')
        db.session.add_all([rest_1, rest_2])
        db.session.commit() # 提交以获取 RestaurantID
        print(f"Created Restaurant: {rest_1.Name} (ID: {rest_1.RestaurantID})")
        print(f"Created Restaurant: {rest_2.Name} (ID: {rest_2.RestaurantID})")

        # --- 4. 创建菜品 (Dish) ---
        # A餐厅的菜品
        dish_a1 = Dish(RestaurantID=rest_1.RestaurantID, Name='红烧肉', BasePrice=15.0,image_url='https://placehold.co/400x200/007bff/white?text=第一食堂')
        dish_a2 = Dish(RestaurantID=rest_1.RestaurantID, Name='番茄炒蛋', BasePrice=8.0,image_url='https://placehold.co/400x200/007bff/white?text=第一食堂')
        dish_a3 = Dish(RestaurantID=rest_1.RestaurantID, Name='米饭', BasePrice=1.0,image_url='https://placehold.co/400x200/007bff/white?text=第一食堂')
        # B餐厅的菜品
        dish_b1 = Dish(RestaurantID=rest_2.RestaurantID, Name='兰州拉面', BasePrice=18.0,image_url='https://placehold.co/400x200/007bff/white?text=第一食堂')
        dish_b2 = Dish(RestaurantID=rest_2.RestaurantID, Name='烤肉串', BasePrice=5.0,image_url='https://placehold.co/400x200/007bff/white?text=第一食堂')
        dish_b3 = Dish(RestaurantID=rest_2.RestaurantID, Name='酸梅汤', BasePrice=3.0,image_url='https://placehold.co/400x200/007bff/white?text=第一食堂')
        db.session.add_all([dish_a1, dish_a2, dish_a3, dish_b1, dish_b2, dish_b3])
        print("Created 6 dishes.")

        # --- 5. 创建用户行为日志 (UserBehaviorLog) - ML的输入 ---
        logs = []
        # Alice (ID=1) -> R1 (ID=1) (常客)
        logs.extend([UserBehaviorLog(UserID=1, RestaurantID=1, ActionType='view_dish') for _ in range(10)])
        logs.extend([UserBehaviorLog(UserID=1, RestaurantID=1, ActionType='add_to_cart') for _ in range(5)])
        logs.extend([UserBehaviorLog(UserID=1, RestaurantID=1, ActionType='order_placed') for _ in range(3)])

        # Bob (ID=2) -> R2 (ID=2) (常客)
        logs.extend([UserBehaviorLog(UserID=2, RestaurantID=2, ActionType='view_dish') for _ in range(12)])
        logs.extend([UserBehaviorLog(UserID=2, RestaurantID=2, ActionType='add_to_cart') for _ in range(4)])
        logs.extend([UserBehaviorLog(UserID=2, RestaurantID=2, ActionType='order_placed') for _ in range(2)])

        # Charlie (ID=3) -> R1 (ID=1) (中等客户)
        logs.extend([UserBehaviorLog(UserID=3, RestaurantID=1, ActionType='view_dish') for _ in range(5)])
        logs.extend([UserBehaviorLog(UserID=3, RestaurantID=1, ActionType='add_to_cart') for _ in range(1)])
        logs.extend([UserBehaviorLog(UserID=3, RestaurantID=1, ActionType='order_placed') for _ in range(1)])

        # David (ID=4) -> R2 (ID=2) (中等客户)
        logs.extend([UserBehaviorLog(UserID=4, RestaurantID=2, ActionType='view_dish') for _ in range(4)])
        logs.extend([UserBehaviorLog(UserID=4, RestaurantID=2, ActionType='order_placed') for _ in range(1)])

        # Eve (ID=5) -> R1 (ID=1) (低价值客户)
        logs.extend([UserBehaviorLog(UserID=5, RestaurantID=1, ActionType='view_dish') for _ in range(1)])

        # Alice (ID=1) -> R2 (ID=2) (低价值客户)
        logs.extend([UserBehaviorLog(UserID=1, RestaurantID=2, ActionType='view_dish') for _ in range(2)])
                
        db.session.add_all(logs)
        print(f"Created {len(logs)} behavior logs (ML Input).")

        # --- 6. 创建商家折扣规则 (MerchantDiscountRule) - 业务规则 ---
        rules = []
        # A餐厅的规则：杀熟，等级越高越贵
        rules.append(MerchantDiscountRule(RestaurantID=rest_1.RestaurantID, PriceLevel=1, Discount=0.8)) # 1级(低价值) 8折
        rules.append(MerchantDiscountRule(RestaurantID=rest_1.RestaurantID, PriceLevel=2, Discount=0.9)) # 2级 9折
        rules.append(MerchantDiscountRule(RestaurantID=rest_1.RestaurantID, PriceLevel=3, Discount=1.0)) # 3级(中等) 原价
        rules.append(MerchantDiscountRule(RestaurantID=rest_1.RestaurantID, PriceLevel=4, Discount=1.1)) # 4级 1.1倍
        rules.append(MerchantDiscountRule(RestaurantID=rest_1.RestaurantID, PriceLevel=5, Discount=1.2)) # 5级(高价值/常客) 1.2倍
        
        # B餐厅的规则：回馈，等级越高越便宜
        rules.append(MerchantDiscountRule(RestaurantID=rest_2.RestaurantID, PriceLevel=1, Discount=1.0)) # 1级(低价值) 原价
        rules.append(MerchantDiscountRule(RestaurantID=rest_2.RestaurantID, PriceLevel=2, Discount=0.95))# 2级 95折
        rules.append(MerchantDiscountRule(RestaurantID=rest_2.RestaurantID, PriceLevel=3, Discount=0.9)) # 3级(中等) 9折
        rules.append(MerchantDiscountRule(RestaurantID=rest_2.RestaurantID, PriceLevel=4, Discount=0.85))# 4级 85折
        rules.append(MerchantDiscountRule(RestaurantID=rest_2.RestaurantID, PriceLevel=5, Discount=0.8)) # 5级(高价值/常客) 8折
        
        db.session.add_all(rules)
        print(f"Created {len(rules)} discount rules (Business Logic).")

        # --- 7. 提交所有更改 ---
        db.session.commit()
        print("\n--- Seeding Complete! ---")
        print(f"Database populated with demo data: {os.path.join(app.instance_path, 'canteen.db')}")

if __name__ == '__main__':
    seed_data()