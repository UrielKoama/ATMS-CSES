from flask import render_template
from . import con
import views


@views.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@views.errorhandler(500)
def internal_error(error):
    con.session.rollback()
    return render_template('500.html'), 500