import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def _database_url():
    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url:
        return url
    return "sqlite:///dev.sqlite"


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        PLATFORM_ADMIN_EMAIL=os.getenv("PLATFORM_ADMIN_EMAIL", "").strip().lower(),
        SQLALCHEMY_DATABASE_URI=_database_url(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=(os.getenv("COOKIE_SECURE", "1" if os.getenv("RENDER") else "0") == "1"),
        REMEMBER_COOKIE_SECURE=(os.getenv("COOKIE_SECURE", "1" if os.getenv("RENDER") else "0") == "1"),
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=__import__("datetime").timedelta(hours=8),
        REMEMBER_COOKIE_HTTPONLY=True,
        WTF_CSRF_TIME_LIMIT=3600,
        DEBUG=os.getenv("FLASK_DEBUG", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)

    # Render runs behind a proxy. Trust one proxy hop for scheme/host information.
    if os.getenv("RENDER"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    @app.template_filter("brasilia")
    def brasilia_datetime(value, fmt="%d/%m/%Y às %H:%M"):
        if value is None:
            return "—"
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(ZoneInfo("America/Sao_Paulo")).strftime(fmt)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre na sua conta para continuar."
    login_manager.login_message_category = "info"

    from app import models  # noqa: F401
    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500

    # Bootstrap only for this first stage. We will replace this with migrations
    # before evolving the production schema.
    with app.app_context():
        db.create_all()
        _upgrade_schema(app)
        _ensure_platform_admin(app)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=()")
        if request_is_https(response):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if response.mimetype in ("application/json", "application/pdf"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    return app


def request_is_https(response):
    from flask import request
    return request.is_secure or bool(os.getenv("RENDER"))


def _upgrade_schema(app):
    """Add subscription columns to existing installs without deleting data."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if "tenants" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("tenants")}
    if "users" in inspector.get_table_names():
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        dialect = db.engine.dialect.name
        if "failed_login_attempts" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"))
        if "login_locked" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN login_locked BOOLEAN NOT NULL DEFAULT FALSE"))
        db.session.commit()
    dialect = db.engine.dialect.name
    additions = {
        "subscription_plan": "VARCHAR(40) NOT NULL DEFAULT 'Mensal'",
        "subscription_expires_at": "TIMESTAMP NULL",
        "whatsapp_number": "VARCHAR(30) NULL",
        "business_type": "VARCHAR(40) NOT NULL DEFAULT 'outros'",
    }
    for column, definition in additions.items():
        if column not in columns:
            if dialect == "sqlite":
                db.session.execute(text(f"ALTER TABLE tenants ADD COLUMN {column} {definition}"))
            else:
                db.session.execute(text(f"ALTER TABLE tenants ADD COLUMN IF NOT EXISTS {column} {definition}"))
    db.session.commit()
    # Additive migration for checkout fields; preserves existing orders.
    if "orders" in inspect(db.engine).get_table_names():
        order_columns = {column["name"] for column in inspect(db.engine).get_columns("orders")}
        order_additions = {
            "delivery_type": "VARCHAR(20) NOT NULL DEFAULT 'Retirada'",
            "payment_method": "VARCHAR(30) NOT NULL DEFAULT 'Pix'",
            "delivery_address": "TEXT NULL",
        }
        for column, definition in order_additions.items():
            if column not in order_columns:
                if dialect == "sqlite":
                    db.session.execute(text(f"ALTER TABLE orders ADD COLUMN {column} {definition}"))
                else:
                    db.session.execute(text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {column} {definition}"))
        db.session.commit()
    # Daily tenant-local order numbers. Additive migration: never deletes existing orders.
    if "orders" in inspect(db.engine).get_table_names():
        order_columns = {column["name"] for column in inspect(db.engine).get_columns("orders")}
        order_additions = {
            "daily_number": "INTEGER NULL",
            "operational_date": "DATE NULL",
        }
        for column, definition in order_additions.items():
            if column not in order_columns:
                if dialect == "sqlite":
                    db.session.execute(text(f"ALTER TABLE orders ADD COLUMN {column} {definition}"))
                else:
                    db.session.execute(text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {column} {definition}"))
        db.session.commit()
        # Backfill legacy orders once, without deleting history, so their displayed
        # numbers do not collide with newly numbered orders in the same business day.
        from datetime import datetime, timezone, timedelta
        from zoneinfo import ZoneInfo
        from app.models import Order
        from sqlalchemy import or_, select, func
        needs_backfill = db.session.scalar(
            select(func.count(Order.id)).where(
                or_(Order.daily_number.is_(None), Order.operational_date.is_(None))
            )
        ) or 0
        if needs_backfill:
            existing_orders = db.session.scalars(
                select(Order).order_by(Order.tenant_id, Order.created_at, Order.id)
            ).all()
            counters = {}
            for order in existing_orders:
                if order.daily_number is not None and order.operational_date is not None:
                    key = (order.tenant_id, order.operational_date)
                    counters[key] = max(counters.get(key, 0), order.daily_number)
                    continue
                created = order.created_at or datetime.now(timezone.utc)
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                local_created = created.astimezone(ZoneInfo("America/Sao_Paulo"))
                cycle_date = local_created.date() if local_created.hour >= 6 else local_created.date() - timedelta(days=1)
                key = (order.tenant_id, cycle_date)
                counters[key] = counters.get(key, 0) + 1
                if order.operational_date is None:
                    order.operational_date = cycle_date
                if order.daily_number is None:
                    order.daily_number = counters[key]
            db.session.commit()

def _ensure_platform_admin(app):
    """Provision the platform owner from Render environment variables."""
    from app.models import Tenant, User
    from sqlalchemy import select
    email = os.getenv("PLATFORM_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("PLATFORM_ADMIN_PASSWORD", "")
    if not email or not password:
        app.logger.warning("Platform admin not provisioned: set PLATFORM_ADMIN_EMAIL and PLATFORM_ADMIN_PASSWORD.")
        return
    # Do not silently skip provisioning based on password length: if the owner
    # configured a password in Render, the same password must be provisioned.
    # Recommend a long password, but never leave the admin account uncreated.
    if len(password) < 12:
        app.logger.warning("PLATFORM_ADMIN_PASSWORD is shorter than recommended; use at least 12 characters.")
    tenant = db.session.scalar(select(Tenant).where(Tenant.slug == "borapedir-platform"))
    if tenant is None:
        tenant = Tenant(name="BoraPedir — Administração", slug="borapedir-platform", is_active=True)
        db.session.add(tenant)
        db.session.flush()
    user = db.session.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
    if user is None:
        user = User(tenant_id=tenant.id, name="Administrador BoraPedir", email=email, role="platform_admin")
        user.set_password(password)
        db.session.add(user)
    else:
        user.role = "platform_admin"
        user.is_active = True
        user.set_password(password)
    db.session.commit()
