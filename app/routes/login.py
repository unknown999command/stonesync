from . import main
from flask import request, render_template, session, redirect, url_for, flash
from app.models import User

@main.route('/login', methods=['GET', 'POST'])
def login():
    # Проверка, авторизован ли пользователь.
    if session.get('user_id'):
        return redirect(url_for('main.index'))  # Перенаправление на главную страницу, если пользователь уже авторизован.
    
    # Обработка POST-запроса для входа.
    if request.method == 'POST':
        password = request.form.get('password')  # Получение пароля из формы.
        user = User.query.filter(User.password == password).first()  # Поиск пользователя по паролю.
        
        if user:
            # Установка данных сессии для авторизованного пользователя.
            session.permanent = True
            session['user_id'] = user.id
            session['user_role'] = user.role
            return redirect(url_for('main.index'))  # Перенаправление на главную страницу.
        else:
            # Вывод сообщения об ошибке при неверном пароле.
            flash('Неверный пароль', 'error')
            return render_template('login.html')  # Отображение страницы входа с ошибкой.

    # Отображение страницы входа для GET-запроса.
    return render_template('login.html')