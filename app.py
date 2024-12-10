from flask import Flask, render_template, request, session, redirect, url_for, flash
from models import db, User, Product, Order, CartItem, add_user, check_user_credentials, get_all_products, add_to_cart, get_cart, checkout
import bcrypt
from sqlalchemy import create_engine, or_, asc, desc
from flask import Flask, render_template, request, redirect, session, flash, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Order  # Импортируем модели User и Order из models.py

app = Flask(__name__)
app.secret_key = 'ssshizi'  # Секретный ключ для сессий

# Настройки базы данных
db_user = 'postgres'
db_password = '1901835'
db_host = 'localhost'  # Или '127.0.0.1', если 'localhost' не работает
db_port = '5432'
db_name = 'marketplace'
engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
Session = sessionmaker(bind=engine)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1901835@localhost:5432/marketplace'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Главная страница с продуктами
@app.route('/')
def index():
    products = get_all_products()
    return render_template('index.html', products=products)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        add_user(username, hashed_password, email)
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Проверяем наличие пользователя и правильность пароля
        session_db = Session()
        user = session_db.query(User).filter_by(username=username).first()
        session_db.close()

        if user and user.password == password:  # Проверяем пароль
            session['username'] = username  # Сохраняем имя пользователя в сессии
            return redirect(url_for('user_profile', user_id=user.id))  # Перенаправляем на страницу профиля
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/user_profile/<int:user_id>')
def user_profile(user_id):
    # Получаем информацию о пользователе из базы данных
    session_db = Session()
    user = session_db.query(User).filter_by(id=user_id).first()
    if user:
        # Получаем все заказы пользователя
        orders = session_db.query(Order).filter_by(user_id=user.id).all()
        session_db.close()

        return render_template('user_profile.html', user=user, orders=orders)  # Отправляем данные пользователя и его заказы
    else:
        flash('User not found', 'error')
        return redirect(url_for('login'))


# Личный кабинет
@app.route('/profile')
def profile():
    username = session.get('username')
    if username:
        # Получаем информацию о пользователе из базы данных
        session_db = Session()
        user = session_db.query(User).filter_by(username=username).first()
        session_db.close()
        
        return render_template('profile.html', user=user)  # Отправляем данные пользователя на страницу профиля
    else:
        flash('You need to log in first.', 'error')
        return redirect(url_for('login'))

# Добавление товара в корзину
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart_route(product_id):
    username = session.get('username')
    if not username:
        flash('Пожалуйста, войдите в систему.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()
    add_to_cart(user.id, product_id)
    flash('Товар добавлен в корзину!', 'success')
    return redirect(url_for('index'))

# Оформление заказа
@app.route('/checkout')
def checkout_route():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    checkout(user.id)
    flash('Ваш заказ оформлен!', 'success')
    return redirect(url_for('profile'))

@app.route('/products', methods=['GET', 'POST'])
def products():
    session_db = Session()

    # Получаем параметры запроса
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'popularity')  # По умолчанию сортируем по популярности
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    # Начинаем с базового запроса
    query = session_db.query(Product)

    # Применяем поиск по названию
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    # Фильтр по категории
    if category_filter:
        query = query.filter(Product.category == category_filter)

    # Фильтр по стоимости
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Сортировка
    if sort_by == 'price_asc':
        query = query.order_by(asc(Product.price))
    elif sort_by == 'price_desc':
        query = query.order_by(desc(Product.price))
    elif sort_by == 'popularity':
        query = query.order_by(desc(Product.created_at))  # Заменяем на популярность при наличии данных

    # Выполняем запрос
    products = query.all()

    # Уникальные категории для фильтрации
    categories = [c[0] for c in session_db.query(Product.category).distinct().all() if c[0]]

    session_db.close()

    return render_template('products.html', products=products, categories=categories)

@app.route('/logout')
def logout():
    session.pop('username', None)  # Удаляем имя пользователя из сессии
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    session_db = Session()

    # Проверяем, есть ли пользователь в сессии
    username = session.get('username')
    if not username:
        flash("Please log in to view your cart.", "error")
        return redirect('/login')

    # Получаем пользователя из базы данных
    user = session_db.query(User).filter_by(username=username).first()
    if not user:
        flash("User not found.", "error")
        return redirect('/login')

    # Получаем элементы корзины пользователя
    cart_items = session_db.query(CartItem).filter_by(user_id=user.id).all()

    # Рассчитываем общую сумму корзины
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    session_db.close()

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

if __name__ == '__main__':
    app.run(debug=True)
