from . import main
from flask import request, render_template, jsonify
from app.models import Order
from .utils.requires_login import requires_login
from datetime import datetime

@main.route('/map', methods=['GET', 'POST'])
@requires_login
def map():
    # Начальный запрос к заказам с определенными статусами.
    query = Order.query.filter(Order.status_id.in_([1, 4]))
    
    if request.method == 'POST':
        # Получение статуса и даты из запроса.
        status = request.form.get('status')  
        date = request.form.get('date')  
        
        # Фильтрация по статусу, если он указан.
        if status:
            try:
                status = int(status)  # Преобразование статуса в целое число.
                query = query.filter_by(status_id=status)  # Применение фильтра.
            except ValueError:
                return jsonify({'error': 'Invalid status format'}), 400  # Ошибка при неверном формате статуса.
        
        # Фильтрация по дате, если она указана.
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()  # Преобразование строки в объект даты.
                query = query.filter(Order.deadline.between(
                    datetime.combine(date_obj, datetime.min.time()), 
                    datetime.combine(date_obj, datetime.max.time())
                ))  # Применение фильтра по диапазону дат.
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400  # Ошибка при неверном формате даты.
        
        # Получение всех заказов, соответствующих фильтрам.
        orders = query.all()  
        return jsonify({  # Возврат заказов в формате JSON.
            'orders': [{
                'address': order.address,
                'price': order.price,
                'phone': order.phone,
                'deadline': order.deadline.isoformat() if order.deadline else None,
                'desc': order.desc,
                'prepayment': order.prepayment,
                'customer': order.customer,
                'status': {'color': order.status.color}
            } for order in orders]
        })
    else:
        # Обработка GET-запроса для отображения карты с заказами.
        orders = query.all()  
        return render_template('map.html', orders=orders)  # Рендеринг страницы карты с заказами.