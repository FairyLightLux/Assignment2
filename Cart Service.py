import os
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tasks.sqlite')
db = SQLAlchemy(app)

PRODUCT_SERVICE_URL = ""

# Cart Model
class Cart(db.Model):
    __tablename__ = "Cart"
    id = db.Column(db.Integer, primary_key=True)
    products = db.relationship("Product", backref="Cart")

class Product(db.Model):
    __tablename__ = "Product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.float, nullable=False)
    quantity_in_cart = db.Column(db.Integer, nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('Cart.id'))

# Endpoint 1: Retrieve current contents of a user's shopping cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_products_in_cart(user_id):
    cart = Cart.query.get(user_id)
    products = cart.products
    product_list = [{"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity_in_cart} for product in products]
    return jsonify({"products": product_list})

# Endpoint 2: Add a specified quantity of a product to the user's cart
@app.route('cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_product_to_cart(user_id, product_id, addQuantity):
    response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}')
    product = response.json()['product']
    if(product['quantity'] < addQuantity):
        addQuantity = product['quantity']
    added_product = Product(id=product['id'], name=product['name'], price=product['price'], quantity=addQuantity, cart_id=user_id)
    db.session.add(added_product)
    db.session.commit()
    
    return jsonify({"message": "Product added", "product": {"id": added_product.id, "name": added_product.name, "price": added_product.price, "quantity": added_product.quantity}}), 201

# Endpoint 3: Remove a specified quantity of a product from the user's cart
@app.route('cart/<int:user_id>/remove<int:product_id>', methods=['POST'])
def remove_product_from_cart(user_id, product_id, removeQuantity):
    cart = Cart.query.get(user_id)
    removed_product = cart.products.query.get(product_id)
    if(removeQuantity < removed_product.quantity):
        removed_product.quantity = removed_product.quantity - removeQuantity
        return jsonify({"message": "Product removed", "product": {"id": removed_product.id, "name": removed_product.name, "price": removed_product.price, "quantity removed": removeQuantity, "quantity remaining": removed_product.quantity}}), 201
    else:
        quantityRemoved = removed_product.quantity
        removed_product.quantity = 0
        return jsonify({"message": "Removed all of product from cart", "product": {"id": removed_product.id, "name": removed_product.name, "price": removed_product.price, "quantity removed": quantityRemoved}}), 201
    
if __name__ == '__main__':
    app.run(debug=True)
    with app.app_context():
        db.create_all