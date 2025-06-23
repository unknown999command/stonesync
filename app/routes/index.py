from . import main
from flask import request, render_template, session
from app.models import Status, Order, View
from .utils.requires_login import requires_login

@main.route('/')
@requires_login
def index():
    # Получение параметра 'tab' из запроса с установкой значения по умолчанию равного 1.
    tab = request.args.get('tab', default=1, type=int)
    
    # Определение фильтров для статусов и заказов в зависимости от значения 'tab'.
    if tab != 1:
        status_filter = [tab]  # Фильтр по выбранному статусу.
        order_filter = Order.status_id == tab  # Фильтрация заказов по статусу.
    else:
        status_filter = [3, 5, 6, 7]  # Фильтруем статусы 3 и 5, если tab равен 1.
        order_filter = ~Order.status_id.in_([3, 5, 6, 7])  # Фильтрация заказов, исключая статусы 3 и 5.
    
    if tab != 1:
        statuses = Status.query.filter(Status.id == tab).all()
    else:
        statuses = Status.query.filter(~Status.id.in_(status_filter)).all()
    
    # Пагинация заказов при условии, что tab равен 5.
    if tab == 5:
        # Получение текущей страницы из запроса (по умолчанию страница 1)
        page = request.args.get('page', default=1, type=int)
        per_page = 200  # Количество заказов на одной странице
        
        # Пагинация запросов с использованием paginate
        orders_pagination = Order.query.filter(order_filter).order_by(Order.deadline.desc()).paginate(page=page, per_page=per_page)
        orders = orders_pagination.items  # Получаем заказы на текущей странице
    else:
        # Загружаем все заказы без пагинации, если tab не равен 5
        orders = Order.query.filter(order_filter).order_by(Order.deadline.asc().nullslast()).all()
    
    # Получение ID пользователя из сессии для дальнейшего использования.
    user_id = session.get('user_id')
    
    # Получение всех просмотров для текущего пользователя.
    views = View.query.filter(View.user_id == user_id).all()
    
    # Подсчет количества ожидающих заказов со статусом 3.
    wait_count = Order.query.filter(Order.status_id == 3).count()
    without_zamer = Order.query.filter(Order.status_id == 6).count()
    without_pay = Order.query.filter(Order.status_id == 7).count()
    
    # Рендеринг страницы с данными о статусах, заказах, просмотрах и количестве ожидающих заказов.
    # Передаем объект `orders_pagination`, если используется пагинация
    return render_template(
        'index.html', 
        statuses=statuses, 
        orders=orders, 
        tab=tab, 
        views=views, 
        wait_count=wait_count, 
        without_zamer=without_zamer, 
        without_pay=without_pay, 
        orders_pagination=orders_pagination if tab == 5 else None
    )
