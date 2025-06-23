from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class='config.Config'):
    app = Flask(__name__)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    app.config.from_object(config_class)

    app.jinja_env.filters['format_phone'] = format_phone_number

    app.secret_key = 'unknownkey'

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import main
    app.register_blueprint(main)

    return app

def format_phone_number(phone):
    if phone and len(phone) == 12 and phone.startswith('+7'):
        return f"{phone[0:2]} ({phone[2:5]}) {phone[5:8]}-{phone[8:10]}-{phone[10:12]}"
    return phone