from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Инициализация SQLAlchemy
db = SQLAlchemy()

# Настройки базы данных
db_user = 'postgres'
db_password = '1901835'
db_host = 'localhost'  # Или '127.0.0.1', если 'localhost' не работает
db_port = '5432'
db_name = 'marketplace'

# Настроим соединение
engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
Session = sessionmaker(bind=engine)

# Base для моделей
Base = declarative_base()

# Модель для пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with orders
    orders = relationship('Order', backref='user', lazy=True)

# Модель для продукта
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с корзиной
    cart_items = relationship('CartItem', backref='product', lazy=True)

# Модель для заказа
class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

# Модель для корзины
class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

# Функции для работы с базой данных

# Добавление пользователя
def add_user(username, password, email):
    session = Session()
    new_user = User(username=username, password=password, email=email)
    session.add(new_user)
    session.commit()
    session.close()

# Проверка логина пользователя
def check_user_credentials(username, password):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    session.close()
    if user and user.password == password:
        return True
    return False

# Получение всех продуктов
def get_all_products():
    session = Session()
    products = session.query(Product).all()
    session.close()
    return products

# Добавление товара в корзину
def add_to_cart(user_id, product_id, quantity=1):
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        session.close()
        return None

    order = session.query(Order).filter_by(user_id=user.id, status='in_cart').first()

    if not order:
        order = Order(user_id=user.id, total_price=0, status='in_cart')
        session.add(order)
        session.commit()

    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        session.close()
        return None

    cart_item = session.query(CartItem).filter_by(order_id=order.id, product_id=product.id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(product_id=product.id, order_id=order.id, quantity=quantity)
        session.add(cart_item)

    order.total_price += product.price * quantity
    session.commit()
    session.close()

# Получение всех товаров в корзине
def get_cart(user_id):
    session = Session()
    order = session.query(Order).filter_by(user_id=user_id, status='in_cart').first()
    if not order:
        session.close()
        return []

    cart_items = session.query(CartItem).filter_by(order_id=order.id).all()
    session.close()
    return cart_items

# Оформление заказа
def checkout(user_id):
    session = Session()
    order = session.query(Order).filter_by(user_id=user_id, status='in_cart').first()
    if order:
        order.status = 'ordered'
        session.commit()
    session.close()
