from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'unknownkey'
    PREFERRED_URL_SCHEME = 'http'
    APPLICATION_ROOT = '/'
    SERVER_NAME = 'stonesync.ru'
    PERMANENT_SESSION_LIFETIME = timedelta(days=365*100)
    users = [
        {'telegram_id': '412500285', 'user_id': '1', 'role': '0', 'name': 'Кирилл'},
        {'telegram_id': '2144506400', 'user_id': '2', 'role': '1', 'name': 'Скуридин'},
        {'telegram_id': '1325862050', 'user_id': '3', 'role': '1', 'name': 'Устимов'},
        {'telegram_id': '1576170266', 'user_id': '4', 'role': '0', 'name': 'Акишин'},
        {'telegram_id': '5336138824', 'user_id': '5', 'role': '0', 'name': 'Виталик'},
        {'telegram_id': '1819582581', 'user_id': '6', 'role': '0', 'name': 'Белорус'},
        {'telegram_id': '5426669376', 'user_id': '7', 'role': '0', 'name': 'Бублик'},
        {'telegram_id': '7425294524', 'user_id': '8', 'role': '0', 'name': 'Дмитрий'}
    ]