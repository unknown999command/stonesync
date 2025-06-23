from app import db
from flask import session
from app.models import View

def old(id, user = ''):
    user = session.get('user_id') if user == '' else user
    view = View.query.filter(View.order_id == id).filter(View.user_id == user).first()
    if view:
        view.is_view = 1
        db.session.commit()
    else:
        new_view = View(user_id = user, order_id=id, is_view=1)
        db.session.add(new_view)
        db.session.commit()