from . import main
from .utils.requires_login import requires_login
from .utils.old import old
from app.models import Order, User, Status, Photo, Comment
from flask import render_template, jsonify
from sqlalchemy import desc
from datetime import datetime

@main.route('/order_details/<int:order_id>')
@requires_login
def order_details(order_id):
    old(order_id)  # Проверка статуса заказа
    
    order = Order.query.get(order_id)  # Получение заказа из БД
    if order is None:  # Проверка на существование заказа
        return jsonify({'error': 'Order not found'}), 404
    
    deadline = order.deadline.strftime("%Y-%m-%dT%H:%M") if order.deadline else None  # Форматирование срока исполнения
    
    # Получение списка пользователей, исключая производителя
    users_query = User.query.filter(User.id != 0)
    if order.manufacturer_id is not None:
        users_query = users_query.filter(User.id != order.manufacturer.id)
    users = users_query.all()
    
    # Получение статусов, исключая текущий статус заказа
    statuses = Status.query.filter(Status.id != order.status.id).all()
    
    # Получение фотографий и комментариев, связанных с заказом
    photos = Photo.query.filter(Photo.order_id == order_id).all()
    messages = Comment.query.filter(Comment.order_id == order_id).order_by(desc(Comment.datetime)).all()
    
    # Рендеринг HTML-шаблона с данными о заказе
    return render_template(
        'order_details.html', 
        order=order, 
        photos=photos, 
        messages=messages, 
        users=users, 
        statuses=statuses, 
        deadline=deadline
    )

def is_image(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Разрешенные расширения изображений
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS  # Проверка расширения