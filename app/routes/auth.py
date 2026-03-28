from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash

from app.extensions import db, limiter
from app.models.user import User
from app.utils.decorators import anonymous_required

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@anonymous_required()
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("auth/login.html", username=username)

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user is None or not user.check_password(password):
            flash("Invalid username or password. Please try again.", "danger")
            return render_template("auth/login.html", username=username)

        if not user.is_active:
            flash(
                "Your account has been disabled. Please contact the administrator.",
                "danger",
            )
            return render_template("auth/login.html", username=username)

        if not user.is_admin:
            flash("You do not have permission to access the admin panel.", "danger")
            return render_template("auth/login.html", username=username)

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.username}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("admin.dashboard"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        flash(
            f"You have been logged out. See you soon, {current_user.username}!", "info"
        )
        logout_user()
    return redirect(url_for("main.index"))
