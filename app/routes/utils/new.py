from app import db
from app.models import User, View
from flask import session

def new(id, user = ''):
    user = session.get('user_id') if user == '' else user
    users = User.query.filter(User.id != user).all()
    views = View.query.filter(View.order_id == id).all()
    views_dict = {view.user_id: view for view in views}
    for user in users:
        if user.id in views_dict:
            view = views_dict[user.id]
            view.is_view = False
            db.session.commit()
        else:
            new_view = View(user_id=user.id, order_id=id, is_view=0)
            db.session.add(new_view)
            db.session.commit()