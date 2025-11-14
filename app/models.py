from . import db  # 从 app.py 导入我们创建的 db 实例
from werkzeug.security import generate_password_hash, check_password_hash
# 1. 基础实体：User
class User(db.Model):
    __tablename__ = 'User'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(80), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(256), nullable=False)
    Area = db.Column(db.String(50))
    # 关系：一个用户可以有多个订单
    Orders = db.relationship('Order', backref='User', lazy=True)
    # 关系：一个用户可以有多个行为日志
    BehaviorLogs = db.relationship('UserBehaviorLog', backref='User', lazy=True)
    # 关系：一个用户可以有多个价格等级
    PriceLevels = db.relationship('UserPriceLevel', backref='User', lazy=True)
    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password)

    # 【新增】校验密码的方法
    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)
# 2. 基础实体：Restaurant

class Restaurant(db.Model):
    __tablename__ = 'Restaurant'
    RestaurantID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MerchantUsername = db.Column(db.String(80), unique=True, nullable=False)
    MerchantPasswordHash = db.Column(db.String(256), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(200))
    image_url = db.Column(db.String(300), nullable=True)
    def set_password(self, password):
        self.MerchantPasswordHash = generate_password_hash(password)

    # 【新增】校验密码的方法
    def check_password(self, password):
        return check_password_hash(self.MerchantPasswordHash, password)

# 3. 基础实体：Dish
class Dish(db.Model):
    __tablename__ = 'Dish'
    DishID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RestaurantID = db.Column(db.Integer, db.ForeignKey('Restaurant.RestaurantID'), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    BasePrice = db.Column(db.Float, nullable=False)
    # 关系：一个菜品可以在多个订单详情中出现
    OrderItems = db.relationship('OrderItem', backref='Dish', lazy=True)
    image_url = db.Column(db.String(300), nullable=True) # <-- 【新增此行】
# 4. 交易核心：Order
class Order(db.Model):
    __tablename__ = 'Order'
    OrderID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    RestaurantID = db.Column(db.Integer, db.ForeignKey('Restaurant.RestaurantID'), nullable=False)
    Status = db.Column(db.String(20), default='Pending') # 例如: Pending, Completed, Cancelled
    TotalPrice = db.Column(db.Float, nullable=False)
    OrderTime = db.Column(db.DateTime, default=db.func.current_timestamp())
    # 关系：一个订单包含多个订单详情
    Items = db.relationship('OrderItem', backref='Order', lazy=True, cascade="all, delete-orphan")

# 5. 交易核心：OrderItem
class OrderItem(db.Model):
    __tablename__ = 'OrderItem'
    OrderItemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('Order.OrderID'), nullable=False)
    DishID = db.Column(db.Integer, db.ForeignKey('Dish.DishID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False, default=1)
    FinalPricePerItem = db.Column(db.Float, nullable=False) # 记录“杀熟”后的最终单价

# --- 这是项目的灵魂 ---

# 6. "DB-ML" 协同核心: UserBehaviorLog (ML输入)
class UserBehaviorLog(db.Model):
    __tablename__ = 'UserBehaviorLog'
    BehaviorLogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    RestaurantID = db.Column(db.Integer, db.ForeignKey('Restaurant.RestaurantID'), nullable=False)
    ActionType = db.Column(db.String(50)) # 例如: 'view_dish', 'add_to_cart', 'order_placed'
    Timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# 7. "DB-ML" 协同核心: UserPriceLevel (ML输出)
class UserPriceLevel(db.Model):
    __tablename__ = 'UserPriceLevel'
    # 这是一个复合主键 (UserID, RestaurantID)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    RestaurantID = db.Column(db.Integer, db.ForeignKey('Restaurant.RestaurantID'), primary_key=True)
    PriceLevel = db.Column(db.Integer, nullable=False) # K-Means 计算出的等级 (例如 1-5)

# 8. "DB-ML" 协同核心: MerchantDiscountRule (业务规则)
class MerchantDiscountRule(db.Model):
    __tablename__ = 'MerchantDiscountRule'
    # 这是一个复合主键 (RestaurantID, PriceLevel)
    RestaurantID = db.Column(db.Integer, db.ForeignKey('Restaurant.RestaurantID'), primary_key=True)
    PriceLevel = db.Column(db.Integer, primary_key=True) # 商家设置的等级 (1-5)
    Discount = db.Column(db.Float, nullable=False, default=1.0) # 例如 0.95 (95折)