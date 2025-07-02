from . import main
from .utils.requires_login import requires_login  # Проверка, что пользователь авторизован
from .utils.new import new  # Обновление состояния (возможно уведомление или статус)
from .utils.createthumbnail import create_thumbnail  # Функция создания миниатюр для изображений
from app.models import Comment, Order, CommentFile, CommentPhoto  # Импорт моделей из базы данных
from app import db  # Работа с базой данных через SQLAlchemy
from flask import request, session, jsonify, current_app  # Импорт фреймворка Flask для обработки запросов
import datetime, asyncio, os, uuid  # Импорт стандартных библиотек для работы с датами, асинхронными операциями, файловой системой и UUID
from datetime import datetime  # Повторный импорт datetime для работы с временными метками

@main.route('/add_comment', methods=['POST'])
@requires_login  # Декоратор для проверки, что пользователь авторизован
def add_comment():
    # Получение корневого пути приложения
    basedir = current_app.root_path
    # Установка путей для загрузки изображений и файлов
    STATIC_FOLDER = os.path.join(basedir, 'static')
    IMAGE_UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'photo')
    FILE_UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'files')

    # Получение текста комментария и ID заказа из формы
    comment_text = request.form.get('comment-text')
    order_id = request.form.get('order_id')
    # Поиск заказа по его ID
    order = Order.query.filter(Order.id == order_id).first()

    # Получение списка загруженных файлов и фильтрация пустых файлов
    files = request.files.getlist('files')
    non_empty_files = [file for file in files if file.filename]
    file_count = len(non_empty_files)  # Подсчет количества загруженных файлов

    # Создание объекта комментария с текущими данными
    comment = Comment(
        datetime=datetime.now(),  # Текущая дата и время
        text=comment_text,
        user_id=session.get('user_id'),  # ID пользователя из сессии
        order_id=order_id  # ID заказа
    )
    db.session.add(comment)  # Добавление комментария в сессию базы данных
    new(order_id, session.get('user_id'))  # Обновление состояния заказа (например, отправка уведомления)
    db.session.commit()  # Сохранение изменений в базе данных

    # Импорт и вызов функции для отправки уведомления о новом комментарии через бота
    from app.bot.notf import send_notification
    # Асинхронная отправка уведомления
    if order:
        attach = f'<b>\n\nПрикреплено: {file_count} файлов</b>' if file_count > 0 else ""  # Если есть файлы, добавляем информацию о них
        asyncio.run(send_notification(
            order.manufacturer_id,
            f"<blockquote>💬 <b>Новый комментарий</b>\n{order.address}</blockquote>\n\n<b>👷 {comment.user.name}\n----------------------------------------</b>\n{comment.text}{attach}", 
            order.id,
            True
        ))
        asyncio.run(send_notification(
            order.manufacturer_id if str(session.get('user_id')) != str(order.manufacturer_id) else '', 
            f"<blockquote>💬 <b>Новый комментарий</b>\n{order.address}</blockquote>\n\n<b>👷 {comment.user.name}\n----------------------------------------</b>\n{comment.text}{attach}", 
            order.id,
            False
        ))

    # Обработка загруженных файлов (сохранение на сервере)
    handle_files(files, comment.id, IMAGE_UPLOAD_FOLDER, FILE_UPLOAD_FOLDER)

    # Получение добавленного комментария из базы данных
    new_comment = Comment.query.get(comment.id)
    # Формирование данных для ответа в формате JSON
    comment_data = {
        'user': new_comment.user.name,
        'color': new_comment.user.color,
        'datetime': new_comment.datetime.strftime('%H:%M %d.%m'),  # Форматирование времени
        'text': new_comment.text,
        'photos': [photo.path for photo in new_comment.comment_photos],  # Пути к фотографиям комментария
        'files': [file.path for file in new_comment.comment_files]  # Пути к файлам комментария
    }
    return jsonify(comment_data), 200  # Возвращаем данные в формате JSON с кодом успеха 200

# Функция проверки, является ли файл изображением по расширению
def is_image(file):
    if file and file.content_type:
        return file.content_type.startswith('image/')
    return False

# Функция для обработки файлов (сохранение изображений и других файлов на сервере)
def handle_files(files, comment_id, image_upload_folder, file_upload_folder):
    for file in files:
        if file and file.filename:  # Если файл существует и имеет имя
            file_extension = os.path.splitext(file.filename)[1]  # Получение расширения файла
            if not file_extension and file.content_type:
                import mimetypes
                file_extension = mimetypes.guess_extension(file.content_type) or '.jpg'
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"  # Создание уникального имени файла с помощью UUID
            if is_image(file):  # Если файл - изображение
                file_path = os.path.join(image_upload_folder, unique_filename)  # Путь для сохранения изображения
                file.save(file_path)  # Сохранение файла на диск
                # Создание миниатюры изображения
                thumbnail_filename = f"small_{unique_filename}"
                thumbnail_path = os.path.join(image_upload_folder, thumbnail_filename)
                create_thumbnail(file_path, thumbnail_path)  # Создание миниатюры с помощью функции
                # Добавление информации о фотографии в базу данных
                db.session.add(CommentPhoto(comment_id=comment_id, path=unique_filename, small_path=thumbnail_filename))
            else:
                # Если файл не изображение, сохраняем его как обычный файл
                file_path = os.path.join(file_upload_folder, unique_filename)
                file.save(file_path)
                # Добавление информации о файле в базу данных
                db.session.add(CommentFile(comment_id=comment_id, path=unique_filename))
    db.session.commit()  # Сохранение всех изменений в базе данных
