from . import main
from flask import session, redirect, url_for
from .utils.requires_login import requires_login

@main.route('/logout')
@requires_login
def logout():
    session.clear()  # Очистка данных сессии.
    return redirect(url_for('main.login'))  # Перенаправление на страницу входа.