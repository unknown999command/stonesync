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
    work_type = request.args.get('type', 'all')
    
    # Получаем всех сотрудников для фильтра
    employees = User.query.filter(User.id != 0).all()
    
    # Получаем данные о зарплате
    salary_data = calculate_salary(employee_id, period, work_type)
    
    return render_template('salary.html', 
                         employees=employees,
                         salary_data=salary_data,
                         selected_employee=employee_id,
                         selected_period=period,
                         selected_type=work_type)

@main.route('/salary_data')
@requires_login
def salary_data():
    """API endpoint для получения данных о зарплате"""
    employee_id = request.args.get('employee', '')
    period = request.args.get('period', '')
    work_type = request.args.get('type', 'all')
    
    salary_data = calculate_salary(employee_id, period, work_type)
    return jsonify(salary_data)

def calculate_salary(employee_id='', period='', work_type='all'):
    """
    Основная функция для расчета зарплаты по дате завершения заказа
    """
    # Базовый запрос для заказов
    orders_query = Order.query
    orders = orders_query.all()
    
    # Словарь для хранения результатов
    salary_results = {}
    total_summary = {
        'orders_count': 0,
        'izgotovlenie_total': 0,
        'montaj_total': 0,
        'total_salary': 0
    }
    
    # Фильтрация по периоду теперь будет по дате завершения
    filtered_orders = []
    period_start = None
    period_end = None
    if period:
        try:
            year, month = period.split('-')
            period_start = datetime(int(year), int(month), 1)
            if int(month) == 12:
                period_end = datetime(int(year) + 1, 1, 1)
            else:
                period_end = datetime(int(year), int(month) + 1, 1)
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
    
    for order, comments, finish_date in filtered_orders:
        izgotovlenie_worker = None
        montaj_worker = None
        izgotovlenie_price = order.izgotovlenie
        montaj_price = order.montaj
        last_workers = {}
        current_status = None
        for comment in comments:
            text = comment.text
            status_match = re.search(r'⏳ Статус: (.+?) -> (.+)', text)
            if status_match:
                old_status = status_match.group(1).strip()
                new_status = status_match.group(2).strip()
                current_status = new_status
            executor_match = re.search(r'👷 Исполнитель: (.+?) -> (.+)', text)
            if executor_match:
                old_executor = executor_match.group(1).strip()
                new_executor = executor_match.group(2).strip()
                if current_status:
                    last_workers[current_status] = new_executor
                if status_match:
                    if new_status == "Изготовление":
                        izgotovlenie_worker = new_executor
                    elif new_status == "Монтаж":
                        montaj_worker = new_executor
        if not izgotovlenie_worker and "Изготовление" in last_workers:
            izgotovlenie_worker = last_workers["Изготовление"]
        if not montaj_worker and "Монтаж" in last_workers:
            montaj_worker = last_workers["Монтаж"]
        if "Завершено" in last_workers:
            if not izgotovlenie_worker:
                for status in ["Изготовление", "Монтаж"]:
                    if status in last_workers:
                        if status == "Изготовление":
                            izgotovlenie_worker = last_workers[status]
                        elif status == "Монтаж":
                            montaj_worker = last_workers[status]
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
        if izgotovlenie_worker and izgotovlenie_price:
            if izgotovlenie_worker not in salary_results:
                salary_results[izgotovlenie_worker] = {
                    'orders_count': 0,
                    'izgotovlenie_total': 0,
                    'montaj_total': 0,
                    'total_salary': 0
                }
            salary_results[izgotovlenie_worker]['izgotovlenie_total'] += izgotovlenie_price
            salary_results[izgotovlenie_worker]['total_salary'] += izgotovlenie_price
            salary_results[izgotovlenie_worker]['orders_count'] += 1
            total_summary['izgotovlenie_total'] += izgotovlenie_price
            total_summary['total_salary'] += izgotovlenie_price
            total_summary['orders_count'] += 1
        if montaj_worker and montaj_price:
            if montaj_worker not in salary_results:
                salary_results[montaj_worker] = {
                    'orders_count': 0,
                    'izgotovlenie_total': 0,
                    'montaj_total': 0,
                    'total_salary': 0
                }
            salary_results[montaj_worker]['montaj_total'] += montaj_price
            salary_results[montaj_worker]['total_salary'] += montaj_price
            salary_results[montaj_worker]['orders_count'] += 1
            total_summary['montaj_total'] += montaj_price
            total_summary['total_salary'] += montaj_price
            total_summary['orders_count'] += 1
    return {
        'employees': salary_results,
        'summary': total_summary
    } 