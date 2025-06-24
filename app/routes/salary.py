from . import main
from flask import render_template, request, jsonify
from .utils.requires_login import requires_login
from app.models import Order, Comment, User
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import re

@main.route('/salary')
@requires_login
def salary():
    # Получаем параметры фильтрации
    employee_id = request.args.get('employee', '')
    period = request.args.get('period', '')
    year = request.args.get('year', '')
    period_type = request.args.get('period_type', 'month')
    work_type = request.args.get('type', 'all')
    
    # Получаем всех сотрудников для фильтра
    employees = User.query.filter(User.id != 0).all()
    
    # Получаем данные о зарплате
    salary_data = calculate_salary(employee_id, period, year, period_type, work_type)
    
    return render_template('salary.html', 
                         employees=employees,
                         salary_data=salary_data,
                         selected_employee=employee_id,
                         selected_period=period,
                         selected_year=year,
                         selected_period_type=period_type,
                         selected_type=work_type)

@main.route('/salary_data')
@requires_login
def salary_data():
    """API endpoint для получения данных о зарплате"""
    employee_id = request.args.get('employee', '')
    period = request.args.get('period', '')
    year = request.args.get('year', '')
    period_type = request.args.get('period_type', 'month')
    work_type = request.args.get('type', 'all')
    
    salary_data = calculate_salary(employee_id, period, year, period_type, work_type)
    return jsonify(salary_data)

def calculate_salary(employee_id='', period='', year='', period_type='month', work_type='all'):
    """
    Основная функция для расчета зарплаты по дате завершения заказа
    """
    # Список сотрудников, которые не участвуют в расчёте зарплаты
    excluded_employees = ['Скуридин', 'Устимов']
    
    # Базовый запрос для заказов
    orders_query = Order.query
    orders = orders_query.all()
    
    # Словарь для хранения результатов
    salary_results = {}
    total_summary = {
        'orders_count': 0,
        'izgotovlenie_total': 0,
        'montaj_total': 0,
        'total_salary': 0,
        'completed_orders': 0,
        'total_orders': len(orders),
        'period_start': None,
        'period_end': None
    }
    
    # Фильтрация по периоду теперь будет по дате завершения
    filtered_orders = []
    period_start = None
    period_end = None
    
    if period_type == 'month' and period:
        try:
            year_val, month = period.split('-')
            period_start = datetime(int(year_val), int(month), 1)
            if int(month) == 12:
                period_end = datetime(int(year_val) + 1, 1, 1)
            else:
                period_end = datetime(int(year_val), int(month) + 1, 1)
            total_summary['period_start'] = period_start
            total_summary['period_end'] = period_end
        except:
            pass
    elif period_type == 'year' and year:
        try:
            year_val = int(year)
            period_start = datetime(year_val, 1, 1)
            period_end = datetime(year_val + 1, 1, 1)
            total_summary['period_start'] = period_start
            total_summary['period_end'] = period_end
        except:
            pass
    
    for order in orders:
        # Получаем комментарии для заказа, отсортированные по дате
        comments = Comment.query.filter(
            Comment.order_id == order.id,
            Comment.user_id == 0  # Только системные комментарии
        ).order_by(Comment.datetime).all()
        
        # Находим дату завершения заказа
        finish_date = None
        for comment in comments:
            if re.search(r'⏳ Статус: .+ -> Завершено', comment.text):
                finish_date = comment.datetime
        # Если не нашли дату завершения — пропускаем заказ
        if not finish_date:
            continue
        # Если выбран период — фильтруем по дате завершения
        if period_start and period_end:
            if not (period_start <= finish_date < period_end):
                continue
        # Добавляем заказ в обработку
        filtered_orders.append((order, comments, finish_date))
    
    total_summary['completed_orders'] = len(filtered_orders)
    
    for order, comments, finish_date in filtered_orders:
        izgotovlenie_worker = None
        montaj_worker = None
        izgotovlenie_price = order.izgotovlenie
        montaj_price = order.montaj
        last_workers = {}
        current_status = None
        
        # Детали заказа для отображения
        order_details = {
            'id': order.id,
            'address': order.address,
            'customer': order.customer,
            'finish_date': finish_date,
            'izgotovlenie_price': izgotovlenie_price,
            'montaj_price': montaj_price,
            'total_price': (izgotovlenie_price or 0) + (montaj_price or 0)
        }
        
        for comment in comments:
            text = comment.text
            status_match = re.search(r'⏳ Статус: (.+?) -> (.+)', text)
            if status_match:
                old_status = status_match.group(1).strip()
                new_status = status_match.group(2).strip()
                current_status = new_status

            executor_match = re.search(r'👷 Исполнитель: (.+?) -> (.+)', text)
            if executor_match:
                new_executor = executor_match.group(2).strip()

                # Определяем, к какому статусу относится смена исполнителя
                effective_status = None
                status_change_at_same_time = False
                for c in comments:
                    if c.datetime == comment.datetime:
                        match = re.search(r'⏳ Статус: .+ -> (.+)', c.text)
                        if match:
                            effective_status = match.group(2).strip()
                            status_change_at_same_time = True
                            break
                
                if not status_change_at_same_time:
                    effective_status = current_status
                
                # Не перезаписываем исполнителя изготовления, если он уже назначен и
                # смена происходит одновременно со сменой статуса на "Монтаж"
                if effective_status == "Изготовление":
                    if not (status_change_at_same_time and any(re.search(r'⏳ Статус: Изготовление -> Монтаж', c.text) for c in comments if c.datetime == comment.datetime)):
                        izgotovlenie_worker = new_executor
                elif effective_status == "Монтаж":
                    montaj_worker = new_executor

        if not izgotovlenie_worker and order.manufacturer_id:
            izgotovlenie_worker = order.manufacturer.name if order.manufacturer else None
        if work_type == 'izgotovlenie' and not izgotovlenie_worker:
            continue
        if work_type == 'montaj' and not montaj_worker:
            continue
        if employee_id:
            employee = User.query.get(employee_id)
            if employee:
                employee_name = employee.name
                if izgotovlenie_worker != employee_name and montaj_worker != employee_name:
                    continue
        
        # Исключаем Скуридина и Устимова из расчётов
        if izgotovlenie_worker in excluded_employees:
            izgotovlenie_worker = None
        if montaj_worker in excluded_employees:
            montaj_worker = None
        
        if izgotovlenie_worker and izgotovlenie_price:
            if izgotovlenie_worker not in salary_results:
                salary_results[izgotovlenie_worker] = {
                    'orders_count': 0,
                    'izgotovlenie_total': 0,
                    'montaj_total': 0,
                    'total_salary': 0,
                    'orders': [],
                    'avg_order_value': 0,
                    'first_order_date': None,
                    'last_order_date': None
                }
            salary_results[izgotovlenie_worker]['izgotovlenie_total'] += izgotovlenie_price
            salary_results[izgotovlenie_worker]['total_salary'] += izgotovlenie_price
            salary_results[izgotovlenie_worker]['orders_count'] += 1
            salary_results[izgotovlenie_worker]['orders'].append({
                **order_details,
                'work_type': 'Изготовление',
                'price': izgotovlenie_price
            })
            if not salary_results[izgotovlenie_worker]['first_order_date'] or finish_date < salary_results[izgotovlenie_worker]['first_order_date']:
                salary_results[izgotovlenie_worker]['first_order_date'] = finish_date
            if not salary_results[izgotovlenie_worker]['last_order_date'] or finish_date > salary_results[izgotovlenie_worker]['last_order_date']:
                salary_results[izgotovlenie_worker]['last_order_date'] = finish_date
            total_summary['izgotovlenie_total'] += izgotovlenie_price
            total_summary['total_salary'] += izgotovlenie_price
            total_summary['orders_count'] += 1
        if montaj_worker and montaj_price:
            if montaj_worker not in salary_results:
                salary_results[montaj_worker] = {
                    'orders_count': 0,
                    'izgotovlenie_total': 0,
                    'montaj_total': 0,
                    'total_salary': 0,
                    'orders': [],
                    'avg_order_value': 0,
                    'first_order_date': None,
                    'last_order_date': None
                }
            salary_results[montaj_worker]['montaj_total'] += montaj_price
            salary_results[montaj_worker]['total_salary'] += montaj_price
            salary_results[montaj_worker]['orders_count'] += 1
            salary_results[montaj_worker]['orders'].append({
                **order_details,
                'work_type': 'Монтаж',
                'price': montaj_price
            })
            if not salary_results[montaj_worker]['first_order_date'] or finish_date < salary_results[montaj_worker]['first_order_date']:
                salary_results[montaj_worker]['first_order_date'] = finish_date
            if not salary_results[montaj_worker]['last_order_date'] or finish_date > salary_results[montaj_worker]['last_order_date']:
                salary_results[montaj_worker]['last_order_date'] = finish_date
            total_summary['montaj_total'] += montaj_price
            total_summary['total_salary'] += montaj_price
            total_summary['orders_count'] += 1
    
    # Вычисляем средние значения и дополнительную статистику
    for employee_data in salary_results.values():
        if employee_data['orders_count'] > 0:
            employee_data['avg_order_value'] = employee_data['total_salary'] / employee_data['orders_count']
            # Сортируем заказы по дате завершения
            employee_data['orders'].sort(key=lambda x: x['finish_date'], reverse=True)
    
    # Сортируем сотрудников по общему заработку
    sorted_employees = dict(sorted(salary_results.items(), key=lambda x: x[1]['total_salary'], reverse=True))
    
    return {
        'employees': sorted_employees,
        'summary': total_summary
    } 