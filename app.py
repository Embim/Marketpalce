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
    session_db = Session()
    
    # Получаем популярные товары (например, последние по времени добавления)
    popular_products = session_db.query(Product).order_by(Product.created_at.desc()).limit(5).all()
    
    # Получаем самые выгодные товары (например, товары с наименьшей ценой)
    best_value_products = session_db.query(Product).order_by(Product.price.asc()).limit(5).all()
    
    session_db.close()
    
    return render_template('index.html', popular_products=popular_products, best_value_products=best_value_products)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  # Пароль сохраняется в открытом виде
        
        add_user(username, password, email)
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

from flask import Flask, request, redirect, render_template, flash, url_for, session
from models import check_user_credentials  # Предположим, что check_user_credentials проверяет данные пользователя

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

        if user and user.password == password:  # Сравниваем пароли в открытом виде
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
def add_to_cart(user_id, product_id, quantity=1):
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        session.close()
        return None

    # Получаем или создаем заказ для пользователя
    order = session.query(Order).filter_by(user_id=user.id, status='in_cart').first()
    if not order:
        order = Order(user_id=user.id, total_price=0, status='in_cart')
        session.add(order)
        session.commit()

    # Получаем продукт
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        session.close()
        return None

    # Проверяем, есть ли товар в корзине
    cart_item = session.query(CartItem).filter_by(user_id=user.id, product_id=product.id).first()

    if cart_item:
        cart_item.quantity += quantity  # Если товар уже в корзине, увеличиваем количество
    else:
        # Добавляем новый товар в корзину
        cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=quantity)
        session.add(cart_item)

    # Обновляем общую цену заказа
    order.total_price += product.price * quantity
    session.commit()
    session.close()

# Страница для добавления товара в корзину
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart_route(product_id):
    username = session.get('username')
    if not username:
        flash('Пожалуйста, войдите в систему.', 'warning')
        return redirect(url_for('login'))

    # Получаем пользователя
    user = db.session.query(User).filter_by(username=username).first()

    # Проверяем, есть ли уже корзина для пользователя
    order = db.session.query(Order).filter_by(user_id=user.id, status='in_cart').first()

    # Если корзины нет, создаем новую
    if not order:
        order = Order(user_id=user.id, total_price=0, status='in_cart')
        db.session.add(order)
        db.session.commit()

    # Получаем продукт
    product = db.session.query(Product).filter_by(id=product_id).first()

    # Если продукт найден
    if product:
        # Проверяем, есть ли товар уже в корзине
        cart_item = db.session.query(CartItem).filter_by(order_id=order.id, product_id=product.id).first()
        if cart_item:
            cart_item.quantity += 1  # Если товар уже есть, увеличиваем количество
        else:
            cart_item = CartItem(product_id=product.id, user_id=user.id, quantity=1, order_id=order.id)  # Используем связь с order
            db.session.add(cart_item)

        # Обновляем общую цену корзины
        order.total_price += product.price
        db.session.commit()
        flash(f'{product.name} добавлен в корзину!', 'success')

    return redirect(url_for('products'))  # Перенаправляем обратно на страницу продуктов




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
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'popularity':
        query = query.order_by(Product.created_at.desc())  # Заменяем на популярность при наличии данных

    # Выполняем запрос
    products = query.all()

    # Получаем список категорий
    categories = session_db.query(Product.category).distinct().all()

    session_db.close()

    return render_template('products.html', products=products, categories=[category[0] for category in categories]) 


@app.route('/product/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    session_db = Session()
    product = session_db.query(Product).get(product_id)  # Используем get для получения продукта по ID
    session_db.close()
    
    if product:
        return render_template('product_detail.html', product=product)
    else:
        flash("Product not found", "error")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)  # Удаляем имя пользователя из сессии
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Страница корзины
@app.route('/cart', methods=['GET', 'POST'])
def cart():
    session_db = db.session

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

@app.route('/remove_from_cart/<int:cart_item_id>', methods=['GET'])
def remove_from_cart(cart_item_id):
    username = session.get('username')
    if not username:
        flash('Please log in to remove items from the cart.', 'warning')
        return redirect(url_for('login'))

    session_db = Session()
    
    # Получаем пользователя из базы данных
    user = session_db.query(User).filter_by(username=username).first()
    if not user:
        flash('User not found.', 'error')
        session_db.close()
        return redirect(url_for('login'))

    # Находим товар в корзине
    cart_item = session_db.query(CartItem).filter_by(id=cart_item_id, user_id=user.id).first()
    if cart_item:
        # Вычитаем стоимость товара из общей суммы заказа
        order = session_db.query(Order).filter_by(user_id=user.id, status='in_cart').first()
        if order:
            order.total_price -= cart_item.product.price * cart_item.quantity
            session_db.commit()

        # Удаляем товар из корзины
        session_db.delete(cart_item)
        session_db.commit()
        flash('Item removed from the cart!', 'success')
    else:
        flash('Item not found in your cart.', 'error')
    
    session_db.close()
    
    return redirect(url_for('cart'))


if __name__ == '__main__':
    app.run(debug=True)
