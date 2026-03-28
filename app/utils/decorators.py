from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Decorator that restricts a view to admin users only.
    Must be used AFTER @login_required so current_user is populated.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def anonymous_required(redirect_to="admin.dashboard"):
    """
    Decorator that redirects already-authenticated users away from
    pages that should only be visible when logged out (e.g. login page).

    Usage::

        @bp.route("/login")
        @anonymous_required()
        def login(): ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                return redirect(url_for(redirect_to))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
