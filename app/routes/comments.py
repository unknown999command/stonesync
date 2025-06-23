from . import main
from flask import request, render_template
from app.models import Comment
from .utils.mask_price import mask_price_and_prepayment
from sqlalchemy import desc
import jwt

@main.route('/comments')
def comments():
    # Извлекаем параметр 'token' из GET-запроса
    token = request.args.get('token')
    
    # Декодируем токен с использованием JWT
    data = jwt.decode(token, 'unknown', algorithms=['HS256'])
    
    # Извлекаем комментарии из базы данных, где order_id совпадает с данным из токена
    # Сортируем результаты по дате создания (datetime) в порядке убывания, т.е. самые новые будут первыми
    messages = Comment.query.filter(Comment.order_id == data['order_id']).order_by(desc(Comment.datetime)).all()
    
    # Обрабатываем каждый комментарий, используя функцию mask_price_and_prepayment, чтобы скрыть или модифицировать цены и предоплаты в тексте
    for message in messages:
        message.text = mask_price_and_prepayment(message.text)
    
    # Возвращаем HTML-шаблон 'comments.html' и передаем в него список комментариев для отображения на веб-странице
    return render_template('comments.html', messages=messages)