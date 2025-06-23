from . import main
from .utils.requires_login import requires_login
from .utils.detect_stone import detectStone
from .utils.format_phone import format_phone_number
from .utils.new import new
from flask import request, jsonify
from app.models import Order, Comment, Status, User
from app import db
import re
import asyncio
from datetime import datetime

@main.route('/edit', methods=['POST'])
@requires_login
def edit():
    try:
        changes = []
        edit_manufacturer = False
        old_manufacturer = ''
        edit = {}
        data = request.get_json()
        data_array = data.get('data', {})
        
        # Извлечение данных из запроса
        id = data_array.get('id')
        customer = data_array.get('customer')
        phone = data_array.get('phone')
        address = data_array.get('address')
        price = None
        prepayment = None
        doplata = data_array.get('doplata') or None
        izgotovlenie = data_array.get('izgotovlenie') or None
        montaj = data_array.get('montaj') or None
        deadline_str = data_array.get('deadline')
        manufacturer_id = data_array.get('manufacturer')
        desc = data_array.get('desc') or None
        status_id = data_array.get('status')

        # Обработка срока выполнения
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None

        # Поиск заказа
        order = Order.query.filter(Order.id == id).first()
        if not order:
            return jsonify({'status': 'error', 'message': 'Заказ не найден'}), 404
        
        # Инициализация переменной изменений
        changes_for_tg = f'<blockquote>✏️ <b>Изменения по заказу\n</b>{order.address}</blockquote>\n\n'

        # Проверка и обновление полей заказа
        def update_field(field_name, new_value, current_value, changes_list):
            """Обновляет поле заказа, если значение изменилось."""
            if new_value != current_value:
                nonlocal changes_for_tg  # Объявляем changes_for_tg как локальную переменную для этой функции
                if isinstance(new_value, datetime):
                    notf = new_value.strftime("%a, %d.%m.%Y / %H:%M")
                    notf_old = ''
                    try:
                        notf_old = current_value.strftime("%a, %d.%m.%Y / %H:%M")
                    except:
                        notf_old = 'Не назначено'
                    changes_for_tg += f"<b>{field_name}</b> {notf}\n"
                    changes_list.append(f"{field_name} {notf_old} -> {notf}")
                else:
                    changes_for_tg += f"<b>{field_name}</b> {new_value if new_value != None else 'Не назначено'}\n"
                    changes_list.append(f"{field_name} {current_value} -> {new_value if new_value != None else 'Не назначено'}")
                return new_value
            return current_value

        # Обновляем поля заказа с помощью вспомогательной функции
        order.customer = update_field("👤 Заказчик:", customer, order.customer, changes)
        order.phone = update_field("📱 Телефон:", phone, order.phone, changes)
        order.address = update_field("🏠 Адрес:", address, order.address, changes)

        # Обработка price и prepayment
        if str(doplata) != str(order.doplata):
            changes.append(f'💵 Доплата: {order.doplata} -> {doplata}')
            order.doplata = None if doplata in [None, 0] else int(doplata)
            changes_for_tg += f"<b>💵 Доплата:</b> {doplata}\n"
        if str(izgotovlenie) != str(order.izgotovlenie):
            changes.append(f'💵 Цена за изготовление: {order.izgotovlenie} -> {izgotovlenie}')
            order.izgotovlenie = None if izgotovlenie in [None, 0] else int(izgotovlenie)
            changes_for_tg += f"<b>💵 Цена за изготовление:</b> {izgotovlenie}\n"
        if str(montaj) != str(order.montaj):
            changes.append(f'💵 Цена за монтаж: {order.montaj} -> {montaj}')
            order.montaj = None if montaj in [None, 0] else int(montaj)
            changes_for_tg += f"<b>💵 Цена за монтаж:</b> {montaj}\n"
            
        order.deadline = update_field("📅 Дата изготовления:", deadline, order.deadline, changes)

        # Обновление статуса заказа
        if status_id and int(status_id) != order.status_id:
            new_status_name = Status.query.filter(Status.id == status_id).first().name
            changes_for_tg += f'⏳ <b>Статус:</b> {new_status_name}\n'
            changes.append(f"⏳ Статус: {order.status.name} -> {new_status_name}")
            order.status_id = int(status_id)
            if int(status_id) == 3 or int(status_id) == 5 or int(status_id) == 6 or int(status_id) == 7:
                manufacturer_id = '0'
                current_time = datetime.now()
                order.deadline = current_time

        # Обновление исполнителя
        if str(manufacturer_id) != str(order.manufacturer_id):
            old_manufacturer = order.manufacturer_id
            edit_manufacturer = True
            new_manufacturer_name = User.query.filter(User.id == manufacturer_id).first().name
            changes_for_tg += f'👷 <b>Исполнитель:</b> {new_manufacturer_name}\n'
            changes.append(f"👷 Исполнитель: {order.manufacturer.name if order.manufacturer else 'Не назначен'} -> {new_manufacturer_name}")
            order.manufacturer_id = int(manufacturer_id) if manufacturer_id.isdigit() else None

        # Обновление описания
        if desc != order.desc:
            formatted_order_desc = order.desc if order.desc is not None else "Нет описания"
            changes_for_tg += f'<b>📄 Описание:</b> {desc if desc is not None else "Нет описания"}\n'
            changes.append(f"📄 Описание: {formatted_order_desc} -> {desc if desc is not None else 'Нет описания'}")
            order.desc = desc
            order.stone = detectStone(desc)

        db.session.commit()

        # Если есть изменения, коммитим и отправляем уведомление
        if changes:
            new(order.id)
            for change in changes:
                new_comment = Comment(text=change, user_id=0, order_id=order.id, datetime=datetime.now())
                db.session.add(new_comment)
            db.session.commit()  # Фиксируем комментарии
            
            from app.bot.notf import send_notification
            if edit_manufacturer:
                asyncio.run(send_notification(manufacturer_id,
                                              f"🔔 У вас появился новый заказ\nАдрес: <a href='https://yandex.ru/maps/?text={order.address}'>{order.address}</a>",
                                              order.id,
                                              False))
                
                asyncio.run(send_notification(old_manufacturer,
                                              f"🔔 Изготовление завершено\nАдрес: <a href='https://yandex.ru/maps/?text={order.address}'>{order.address}</a>",
                                              order.id,
                                              False,
                                              False))
            else:
                asyncio.run(send_notification(order.manufacturer_id,
                                              changes_for_tg,
                                              order.id,
                                              False))
            asyncio.run(send_notification('',
                                          changes_for_tg,
                                          order.id,
                                          True))
        else:
            print(f"Никаких изменений для заказа {id} не было.")

        # Формируем ответ для клиента
        manufacturer_name = order.manufacturer.name if order.manufacturer else "Не назначен"
        manufacturer_id = order.manufacturer.id if order.manufacturer else ""
        
        edit = {
            'customer': customer,
            'format_phone': format_phone_number(phone),
            'phone': phone,
            'address': address,
            'price': order.price,
            'prepayment': order.prepayment,
            'doplata': order.doplata,
            'izgotovlenie': order.izgotovlenie,
            'montaj': order.montaj,
            'deadline': order.deadline.strftime('%Y-%m-%dT%H:%M') if order.deadline else None,
            'manufacturer': manufacturer_name,
            'manufacturer_id': manufacturer_id,
            'desc': desc,
            'status': order.status.name,
            'status_id': order.status.id,
            'status_color': order.status.color,
            'stone': order.stone
        }

        return jsonify({'status': 'success', 'changes': changes, 'edit': edit}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
