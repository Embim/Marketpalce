from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
# from models import db, User, Product
# from config import Config
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import psycopg2

app = Flask(__name__)
# app.config.from_object()
# db.init_app(app)



# # Настройки базы данных
# db_user = 'postgres'
# db_password = '1901835'
# db_host = 'localhost'  # Или '127.0.0.1', если 'localhost' не работает
# db_port = '5432'
# db_name = 'marketplace'
# engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
# Session = sessionmaker(bind=engine)


@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/')
# def index():
#     products = Product.query.all()
#     return render_template('index.html', products=products)

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = request.form['password']
#         new_user = User(username=username, email=email, password=password)
#         db.session.add(new_user)
#         db.session.commit()
#         return redirect(url_for('index'))
#     return render_template('register.html')

# @app.route('/products')
# def products():
#     products = Product.query.all()
#     return render_template('products.html', products=products)

# @app.route('/add_product', methods=['GET', 'POST'])
# def add_product():
#     if request.method == 'POST':
#         name = request.form['name']
#         description = request.form['description']
#         price = request.form['price']
#         category = request.form['category']
#         new_product = Product(name=name, description=description, price=price, category=category)
#         db.session.add(new_product)
#         db.session.commit()
#         return redirect(url_for('products'))
#     return render_template('add_product.html')

if __name__ == '__main__':
    app.run(debug=True)
