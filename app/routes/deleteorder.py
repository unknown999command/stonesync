from . import main
from .utils.requires_login import requires_login
from .utils.remove_file import remove_file
from flask import request
from app.models import CommentFile, CommentPhoto, Comment, View, Order, Photo
from app import db
import os

@main.route('/deleteorder', methods=['POST'])
@requires_login
def deleteOrder():    
    PHOTO_DIR = 'app/static/photo'  # Директория для фотографий
    FILE_DIR = 'app/static/files'    # Директория для файлов
    data = request.get_json()        # Получение данных из запроса
    order_id = data.get('order_id')  # Получение ID заказа из данных
    
    # Удаление фотографий, связанных с заказом
    delete_photos(order_id, PHOTO_DIR)
    
    # Удаление комментариев, связанных с заказом
    delete_comments(order_id, PHOTO_DIR, FILE_DIR)
    
    # Удаление просмотров и самого заказа
    View.query.filter(View.order_id == order_id).delete()
    Order.query.filter(Order.id == order_id).delete()
    
    # Подтверждение всех удалений в базе данных
    db.session.commit()
    
    return '', 200

def delete_photos(order_id, photo_dir):
    """Удаляет фотографии, связанные с заданным order_id."""
    photos = Photo.query.filter(Photo.order_id == order_id).all()  # Получение всех фотографий для заказа
    for photo in photos:
        remove_file(photo_dir, photo.path)  # Удаление основной фотографии
        remove_file(photo_dir, photo.small_path)  # Удаление уменьшенной фотографии, если она есть
        db.session.delete(photo)  # Удаление записи фотографии из базы данных

def delete_comments(order_id, photo_dir, file_dir):
    """Удаляет комментарии и связанные с ними фотографии и файлы, относящиеся к заданному order_id."""
    comments = Comment.query.filter(Comment.order_id == order_id).all()  # Получение всех комментариев для заказа
    for comment in comments:
        # Удаление фотографий комментариев
        delete_comment_photos(comment.id, photo_dir)
        
        # Удаление файлов комментариев
        delete_comment_files(comment.id, file_dir)
        
        db.session.delete(comment)  # Удаление записи комментария из базы данных

def delete_comment_photos(comment_id, photo_dir):
    """Удаляет фотографии, связанные с комментарием."""
    comment_photos = CommentPhoto.query.filter(CommentPhoto.comment_id == comment_id).all()  # Получение всех фотографий комментария
    for comment_photo in comment_photos:
        remove_file(photo_dir, comment_photo.path)  # Удаление основной фотографии комментария
        remove_file(photo_dir, comment_photo.small_path)  # Удаление уменьшенной фотографии комментария, если она есть
        db.session.delete(comment_photo)  # Удаление записи фотографии комментария из базы данных

def delete_comment_files(comment_id, file_dir):
    """Удаляет файлы, связанные с комментарием."""
    comment_files = CommentFile.query.filter(CommentFile.comment_id == comment_id).all()  # Получение всех файлов комментария
    for comment_file in comment_files:
        remove_file(file_dir, comment_file.path)  # Удаление файла комментария
        db.session.delete(comment_file)  # Удаление записи файла комментария из базы данных