from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Integer, nullable=False)

class Status(db.Model):
    __tablename__ = 'statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False)
    price = db.Column(db.Integer, nullable=True)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)
    desc = db.Column(db.Text, nullable=True)
    stone = db.Column(db.Text, nullable=True)
    prepayment = db.Column(db.Integer, nullable=True)
    doplata = db.Column(db.Integer, nullable=True)
    izgotovlenie = db.Column(db.Integer, nullable=True)
    montaj = db.Column(db.Integer, nullable=True)
    customer = db.Column(db.String(100), nullable=False)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    status = db.relationship('Status')
    manufacturer = db.relationship('User', foreign_keys=[manufacturer_id])
    photos = db.relationship('Photo')
    comments = db.relationship('Comment')

class View(db.Model):
    __tablename__ = 'views'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    is_view = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order')
    user = db.relationship('User')

class Photo(db.Model):
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    small_path = db.Column(db.String(255), nullable=True)

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    user = db.relationship('User')
    comment_photos = db.relationship('CommentPhoto')
    comment_files = db.relationship('CommentFile')

class CommentPhoto(db.Model):
    __tablename__ = 'comment_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    small_path = db.Column(db.String(255), nullable=True)

class CommentFile(db.Model):
    __tablename__ = 'comment_files'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    path = db.Column(db.String(255), nullable=False)
