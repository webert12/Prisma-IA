import re
import unicodedata

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Tenant, User
from app.catalog import CATALOGS, seed_catalog

bp = Blueprint("auth", __name__, url_prefix="/auth")


def make_slug(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return (slug[:70] or "empresa")


@bp.route("/cadastro", methods=["GET", "POST"])
def register():
    # Cadastro público desativado: contas são provisionadas pela administração.
    from flask import abort
    abort(404)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "platform_admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        import os
        configured_admin_email = os.getenv("PLATFORM_ADMIN_EMAIL", "").strip().lower()
        users = db.session.scalars(
            select(User).where(User.email == email).order_by(User.id.asc())
        ).all()
        # Se o e-mail do administrador estiver configurado, só a conta com papel
        # platform_admin pode autenticar nesse endereço.
        if configured_admin_email and email == configured_admin_email:
            users = [u for u in users if u.role == "platform_admin"]
        else:
            users = [u for u in users if u.role != "platform_admin"]

        user = users[0] if users else None
        if user and user.login_locked:
            flash("Acesso bloqueado após 3 tentativas. Solicite ao administrador o desbloqueio da conta.", "error")
            return render_template("auth/login.html"), 403

        valid = bool(user and user.is_active and user.tenant.is_active and user.check_password(password))
        if valid:
            user.failed_login_attempts = 0
            db.session.commit()
            login_user(user, remember=False)
            if user.role == "platform_admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("main.dashboard"))

        if user and user.is_active:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 3:
                user.login_locked = True
            db.session.commit()
            if user.login_locked:
                flash("Conta bloqueada após 3 tentativas. Peça ao administrador para desbloquear.", "error")
            else:
                flash("E-mail ou senha inválidos.", "error")
        else:
            flash("E-mail ou senha inválidos.", "error")

    return render_template("auth/login.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))
