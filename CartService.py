import os
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'carts.sqlite')
db = SQLAlchemy(app)

PRODUCT_SERVICE_URL = "http://localhost:5000"

# Cart Model
class Cart(db.Model):
    __tablename__ = "Cart"
    id = db.Column(db.Integer, primary_key=True)
    products = db.relationship("Product", backref="Cart")

class Product(db.Model):
    __tablename__ = "Product"
    cart_id = db.Column(db.Integer, db.ForeignKey('Cart.id'), primary_key=True)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity_in_cart = db.Column(db.Integer, nullable=False)
    
    
# Endpoint 0: Print all carts to test
@app.route('/cart', methods=['GET'])
def get_products():
    carts = Cart.query.all()
    cart_list = []
    for cart in carts:
        productList = [{"id":product.id, "name":product.name, "price":product.price, "quantity":product.quantity_in_cart} for product in cart.products]
        cart_list += [{"id":cart.id, "products":productList}]
    return jsonify({"carts": cart_list})

# Endpoint 1: Retrieve current contents of a user's shopping cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_products_in_cart(user_id):
    
    # If a cart doesn't exist for this user, create one
    cart = Cart.query.get(user_id)
    if not cart:
        cart = Cart(id=user_id)
        db.session.add(cart)
        db.session.commit()

    products = cart.products
    product_list = [{"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity_in_cart} for product in products]
    return jsonify({"id": cart.id, "products": product_list})

# Endpoint 2: Add a specified quantity of a product to the user's cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_product_to_cart(user_id, product_id):
    
    # If a cart doesn't exist for this user, create one
    cart = Cart.query.get(user_id)
    if not cart:
        cart = Cart(id=user_id)
        db.session.add(cart)
        db.session.commit()

    data = request.json
    if "quantity" not in data:
        return jsonify({"error": "quantity is required"}), 400
    addQuantity = data["quantity"]

    # Retrieve product info from the product service
    requestsURL = f'{PRODUCT_SERVICE_URL}/products/{product_id}'
    response = requests.get(requestsURL)
    data = response.json()
    
    if "product" not in data:
        return jsonify({"error":"Product not listed in inventory"}), 404
    product = response.json()["product"]
    
    if(product['quantity'] < addQuantity):
        return jsonify({"error":f"Quantity of {addQuantity} requested but quantity in inventory is {product['quantity']}"}), 404
    
    existingProduct = next((item for item in cart.products if item.id == product_id), None)    
    if(existingProduct):
        existingProduct.quantity_in_cart += addQuantity
        db.session.commit()
        return jsonify({"message": "Product added to cart", "product": {"id": existingProduct.id, "name": existingProduct.name, "price": existingProduct.price, "added quantity": addQuantity, "new quantity": existingProduct.quantity_in_cart}}), 201
    else:
        added_product = Product(id=product['id'], name=product['name'], price=product['price'], quantity_in_cart=addQuantity, cart_id=user_id)
        db.session.add(added_product)
        db.session.commit()
        return jsonify({"message": "Product added to cart", "product": {"id": added_product.id, "name": added_product.name, "price": added_product.price, "quantity": added_product.quantity_in_cart}}), 201

# Endpoint 3: Remove a specified quantity of a product from the user's cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['POST'])
def remove_product_from_cart(user_id, product_id):
    cart = Cart.query.get(user_id)
    if not cart:
        return jsonify({"error":"That cart does not exist"})
    
    data = request.json
    if "quantity" not in data:
        return jsonify({"error": "quantity is required"}), 400
    removeQuantity = data["quantity"]

    removedProduct = next((item for item in cart.products if item.id == product_id), None)    
    if not (removedProduct):
        return jsonify({"error":"That item is not in this cart"})  
    else:

        if(removeQuantity <= removedProduct.quantity_in_cart):
            removedProduct.quantity_in_cart = removedProduct.quantity_in_cart - removeQuantity
            db.session.commit()
            return jsonify({"message": "Product removed", "product": {"id": removedProduct.id, "name": removedProduct.name, "price": removedProduct.price, "quantity removed": removeQuantity, "quantity remaining": removedProduct.quantity_in_cart}}), 201
        else:
            quantityRemoved = removedProduct.quantity_in_cart
            removedProduct.quantity_in_cart = 0
            db.session.commit()
            return jsonify({"message": "Removed all of product from cart", "product": {"id": removedProduct.id, "name": removedProduct.name, "price": removedProduct.price, "quantity removed": quantityRemoved}}), 201
    
if __name__ == '__main__':
    app.run(debug=True,port=5001)

with app.app_context():
    print("Creating database...")
    db.create_all()
    print("Database created!")