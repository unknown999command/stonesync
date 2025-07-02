from flask import Blueprint

main = Blueprint('main', __name__)

from . import index, login, logout, create, map, order_detail, edit, comments, deleteorder, addcomment, addphoto, salary