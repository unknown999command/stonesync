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
    Основная функция для расчета зарплаты
    """
    # Базовый запрос для заказов
    orders_query = Order.query
    
    # Фильтрация по периоду
    if period:
        try:
            year, month = period.split('-')
            start_date = datetime(int(year), int(month), 1)
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1)
            else:
                end_date = datetime(int(year), int(month) + 1, 1)
            
            orders_query = orders_query.filter(
                Order.date >= start_date,
                Order.date < end_date
            )
        except:
            pass
    
    orders = orders_query.all()
    
    # Словарь для хранения результатов
    salary_results = {}
    total_summary = {
        'orders_count': 0,
        'izgotovlenie_total': 0,
        'montaj_total': 0,
        'total_salary': 0
    }
    
    for order in orders:
        # Получаем комментарии для заказа, отсортированные по дате
        comments = Comment.query.filter(
            Comment.order_id == order.id,
            Comment.user_id == 0  # Только системные комментарии
        ).order_by(Comment.datetime).all()
        
        # Анализируем логи для определения исполнителей
        izgotovlenie_worker = None
        montaj_worker = None
        izgotovlenie_price = order.izgotovlenie
        montaj_price = order.montaj
        
        # Словарь для отслеживания последних исполнителей по статусам
        last_workers = {}
        current_status = None
        
        # Проходим по всем комментариям в хронологическом порядке
        for comment in comments:
            text = comment.text
            
            # Поиск изменения статуса
            status_match = re.search(r'⏳ Статус: (.+?) -> (.+)', text)
            if status_match:
                old_status = status_match.group(1).strip()
                new_status = status_match.group(2).strip()
                current_status = new_status
            
            # Поиск назначения исполнителя
            executor_match = re.search(r'👷 Исполнитель: (.+?) -> (.+)', text)
            if executor_match:
                old_executor = executor_match.group(1).strip()
                new_executor = executor_match.group(2).strip()
                
                # Сохраняем последнего исполнителя для каждого статуса
                if current_status:
                    last_workers[current_status] = new_executor
                
                # Если в том же комментарии есть изменение статуса
                if status_match:
                    if new_status == "Изготовление":
                        izgotovlenie_worker = new_executor
                    elif new_status == "Монтаж":
                        montaj_worker = new_executor
        
        # Если не определили исполнителей через изменения статуса,
        # берем последних исполнителей для соответствующих статусов
        if not izgotovlenie_worker and "Изготовление" in last_workers:
            izgotovlenie_worker = last_workers["Изготовление"]
        
        if not montaj_worker and "Монтаж" in last_workers:
            montaj_worker = last_workers["Монтаж"]
        
        # Если заказ завершен, проверяем последних исполнителей
        if "Завершено" in last_workers:
            # Если не определили изготовителя, берем последнего исполнителя перед завершением
            if not izgotovlenie_worker:
                # Ищем последнего исполнителя для статуса "Изготовление" или "Монтаж"
                for status in ["Изготовление", "Монтаж"]:
                    if status in last_workers:
                        if status == "Изготовление":
                            izgotovlenie_worker = last_workers[status]
                        elif status == "Монтаж":
                            montaj_worker = last_workers[status]
        
        # Если не нашли в логах, берем из текущего состояния заказа
        if not izgotovlenie_worker and order.manufacturer_id:
            izgotovlenie_worker = order.manufacturer.name if order.manufacturer else None
        
        # Фильтрация по типу работы
        if work_type == 'izgotovlenie' and not izgotovlenie_worker:
            continue
        if work_type == 'montaj' and not montaj_worker:
            continue
        
        # Фильтрация по сотруднику
        if employee_id:
            employee = User.query.get(employee_id)
            if employee:
                employee_name = employee.name
                if izgotovlenie_worker != employee_name and montaj_worker != employee_name:
                    continue
        
        # Подсчет зарплаты
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