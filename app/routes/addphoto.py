from . import main
from .utils.requires_login import requires_login
from .utils.createthumbnail import create_thumbnail
from .utils.new import new
from app import db
from app.models import Photo, Order, Comment
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os, asyncio, datetime, uuid
from datetime import datetime
import mimetypes

# --- Поддержка HEIC/HEIF ---
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print('ВНИМАНИЕ: pillow-heif не установлен, HEIC/HEIF не поддерживается!')

from PIL import Image

def log_file_info(file):
    print('filename:', file.filename)
    print('content_type:', file.content_type)
    print('ext:', os.path.splitext(file.filename)[1])
    print('guessed_ext:', mimetypes.guess_extension(file.content_type))

@main.route('/addphoto', methods=['POST'])
@requires_login
def addphoto():
    files = request.files.getlist('photos')
    count = str(len(files))
    order_id = request.form.get('order_id')

    saved_files = []

    basedir = current_app.root_path
    STATIC_FOLDER = os.path.join(basedir, 'static')
    upload_folder = os.path.join(STATIC_FOLDER, 'photo')

    for file in files:
        if file and file.filename and file.content_type and file.content_type.startswith('image/'):
            log_file_info(file)
            file_ext = os.path.splitext(file.filename)[1]
            if not file_ext:
                # Если у файла нет расширения, пытаемся его угадать по MIME-типу
                file_ext = mimetypes.guess_extension(file.content_type) or '.jpg'
            
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)

            # --- Обработка HEIC/HEIF: конвертация в JPEG для миниатюры ---
            small_filename = f"small_{unique_filename}"
            small_filepath = os.path.join(upload_folder, small_filename)
            try:
                if file_ext.lower() in ['.heic', '.heif']:
                    with Image.open(file_path) as img:
                        # Конвертируем в JPEG для миниатюры
                        rgb_img = img.convert('RGB')
                        temp_jpeg = file_path + '.jpg'
                        rgb_img.save(temp_jpeg, 'JPEG')
                        create_thumbnail(temp_jpeg, small_filepath)
                        os.remove(temp_jpeg)
                else:
                    create_thumbnail(file_path, small_filepath)
            except Exception as e:
                print(f'Ошибка при создании миниатюры для {file_path}:', e)
                small_filename = None
                small_filepath = None

            photo = Photo(order_id=order_id, path=unique_filename, small_path=small_filename)
            db.session.add(photo)
            saved_files.append({
                'full_size': unique_filename,
                'thumbnail': small_filename
            })

    new(order_id)
    db.session.commit()

    order = Order.query.filter(Order.id == order_id).first()
    if order:
        from app.bot.notf import send_notification
        asyncio.run(send_notification(order.manufacturer_id,
                                      f'<blockquote><b>✏️ Изменения по заказу\n</b>{order.address}</blockquote>\n\n<b>📷 Новые фото:</b> {str(len(files))} шт.',
                                      order.id,
                                      False))
        asyncio.run(send_notification(order.manufacturer_id,
                                      f'<blockquote><b>✏️ Изменения по заказу\n</b>{order.address}</blockquote>\n\n<b>📷 Новые фото:</b> {str(len(files))} шт.',
                                      order.id,
                                      True))
    new_comment = Comment(
        text="Добавленно " + str(len(files)) + " фото",
        user_id=0,
        order_id=order_id,
        datetime=datetime.now()
    )

    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'message': 'Файлы успешно загружены', 'files': saved_files, 'count': count}), 200

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic', 'heif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS