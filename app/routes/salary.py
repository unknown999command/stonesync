from . import main
from flask import render_template
from .utils.requires_login import requires_login

@main.route('/salary')
@requires_login
def salary():
    return render_template('salary.html') 