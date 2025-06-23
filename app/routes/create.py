from . import main
from flask import request, flash, render_template, redirect, url_for, current_app
from app import db
from .utils.requires_login import requires_login
from .utils.detect_stone import detectStone
from .utils.new import new
from .utils.createthumbnail import create_thumbnail
from app.models import Order, User, Status, Photo
from PIL import Image
import datetime, os, asyncio, uuid
from datetime import datetime

@main.route('/create', methods=['GET', 'POST'])
@requires_login
def create():
    if request.method == 'POST':
        try:
            status_id = request.form.get('status')
            customer = request.form.get('customer')
            phone = request.form.get('phone')
            address = request.form.get('address')
            doplata = request.form.get('doplata')
            izgotovlenie = request.form.get('izgotovlenie')
            montaj = request.form.get('montaj')
            desc = request.form.get('desc')
            if desc == '':
                desc = None
            stone = detectStone(desc)
            deadline = request.form.get('deadline')
            manufacturer_id = request.form.get('manufacturer', '').strip()
            doplata = int(doplata) if doplata else None
            izgotovlenie = int(izgotovlenie) if izgotovlenie else None
            montaj = int(montaj) if montaj else None
            deadline = datetime.strptime(deadline, '%Y-%m-%dT%H:%M') if deadline else None
            manufacturer_id = int(manufacturer_id) if manufacturer_id else None
            new_order = Order(
                status_id=status_id,
                customer=customer,
                phone=phone,
                address=address,
                price=0,
                prepayment=0,
                doplata=doplata,
                izgotovlenie=izgotovlenie,
                montaj=montaj,
                desc=desc,
                deadline=deadline,
                manufacturer_id=manufacturer_id,
                stone=stone
            )
            db.session.add(new_order)
            db.session.commit()
            order_id = new_order.id

            from app.bot.notf import send_notification
            asyncio.run(send_notification(manufacturer_id,
                                          f"<blockquote>🔔 Новый заказ</blockquote>\n🏠 Адрес: <a href='https://yandex.ru/maps/?text={new_order.address}'>{new_order.address}</a>",
                                          order_id,
                                          False))
            
            asyncio.run(send_notification('',
                                          f"<blockquote>🔔 Новый заказ\n{new_order.address}</blockquote>",
                                          order_id,
                                          True))

            new(order_id)
            basedir = current_app.root_path
            STATIC_FOLDER = os.path.join(basedir, 'static')
            upload_folder = os.path.join(STATIC_FOLDER, 'photo')

            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and photo.filename:
                    if photo.content_type.startswith('image/'):
                        file_ext = os.path.splitext(photo.filename)[1]
                        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                        filepath = os.path.join(upload_folder, unique_filename)
                        photo.save(filepath)

                        small_filename = f"small_{unique_filename}"
                        small_filepath = os.path.join(upload_folder, small_filename)
                        
                        try:
                            create_thumbnail(filepath, small_filepath)

                            new_photo = Photo(
                                order_id=new_order.id,
                                path=unique_filename,
                                small_path=small_filename
                            )
                            db.session.add(new_photo)
                        except:
                            pass
                    else:
                        pass
            db.session.commit()
            return redirect(url_for('main.index'))
        except:
            db.session.rollback()
    manufacturers = User.query.filter(User.id != 0).all()
    statuses = Status.query.all()
    return render_template('create_order.html', statuses=statuses, manufacturers=manufacturers)