import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app import db
from app.models import Tenant, User, utc_now
from app.auth import make_slug
from app.catalog import seed_catalog
import re

bp = Blueprint("admin", __name__, url_prefix="/admin")

def is_platform_admin(user):
    configured_email = os.getenv("PLATFORM_ADMIN_EMAIL", "").strip().lower()
    return bool(configured_email and user.is_authenticated and user.email.lower() == configured_email and user.role == "platform_admin")

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not is_platform_admin(current_user):
            abort(403)
        return view(*args, **kwargs)
    return wrapped

@bp.get("/")
@admin_required
def dashboard():
    tenants = db.session.scalars(select(Tenant).order_by(Tenant.created_at.desc())).all()
    tenant_count = db.session.scalar(select(func.count(Tenant.id))) or 0
    user_count = db.session.scalar(select(func.count(User.id)).where(User.role != "platform_admin")) or 0
    active_count = db.session.scalar(select(func.count(Tenant.id)).where(Tenant.is_active.is_(True))) or 0
    return render_template("admin/dashboard.html", tenants=tenants, tenant_count=tenant_count, user_count=user_count, active_count=active_count)


@bp.route("/empresa/nova", methods=["GET", "POST"])
@admin_required
def create_tenant():
    if request.method == "POST":
        owner_name = request.form.get("owner_name", "").strip()
        tenant_name = request.form.get("tenant_name", "").strip()
        whatsapp = re.sub(r"\D", "", request.form.get("whatsapp_number", ""))
        if len(whatsapp) in (10, 11):
            whatsapp = "55" + whatsapp
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account_type = request.form.get("account_type", "active30")
        business_type = request.form.get("business_type", "outros").strip().lower()
        if not owner_name or len(owner_name) > 120 or not tenant_name or len(tenant_name) > 120:
            flash("Informe o nome do cliente e o nome da empresa (até 120 caracteres).", "error")
            return redirect(url_for("admin.create_tenant"))
        if not (10 <= len(whatsapp) <= 15):
            flash("Informe um WhatsApp válido com DDD.", "error")
            return redirect(url_for("admin.create_tenant"))
        if "@" not in email or len(email) > 255:
            flash("Informe um e-mail válido.", "error")
            return redirect(url_for("admin.create_tenant"))
        if email == os.getenv("PLATFORM_ADMIN_EMAIL", "").strip().lower():
            flash("Esse e-mail está reservado para a administração da plataforma.", "error")
            return redirect(url_for("admin.create_tenant"))
        if db.session.scalar(select(User.id).where(User.email == email)) is not None:
            flash("Esse e-mail já está em uso. Cada cliente precisa de um e-mail de acesso exclusivo.", "error")
            return redirect(url_for("admin.create_tenant"))
        if len(password) < 10 or len(password) > 128:
            flash("A senha inicial deve ter entre 10 e 128 caracteres.", "error")
            return redirect(url_for("admin.create_tenant"))
        if account_type not in {"active30", "trial"}:
            account_type = "active30"
        try:
            trial_days = int(request.form.get("trial_days", "7")) if account_type == "trial" else 30
        except (TypeError, ValueError):
            trial_days = 0
        if not 1 <= trial_days <= 365:
            flash("Os dias de teste devem estar entre 1 e 365.", "error")
            return redirect(url_for("admin.create_tenant"))
        valid_types = {"hamburgueria", "lanchonete", "pizzaria", "restaurante", "doceria", "cafeteria", "outros_alimentos", "outros"}
        if business_type not in valid_types:
            business_type = "outros"
        base_slug = make_slug(tenant_name)
        slug = base_slug
        suffix = 2
        while db.session.scalar(select(Tenant.id).where(Tenant.slug == slug)) is not None:
            slug = f"{base_slug[:65]}-{suffix}"
            suffix += 1
        days = 30 if account_type == "active30" else trial_days
        plan = "Mensal" if account_type == "active30" else f"Teste ({days} dias)"
        tenant = Tenant(
            name=tenant_name, slug=slug, whatsapp_number=whatsapp,
            business_type=business_type, is_active=True, subscription_plan=plan,
            subscription_expires_at=utc_now() + timedelta(days=days),
        )
        try:
            db.session.add(tenant)
            db.session.flush()
            owner = User(tenant_id=tenant.id, name=owner_name, email=email, role="owner", is_active=True)
            owner.set_password(password)
            db.session.add(owner)
            seed_catalog(tenant, business_type)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao criar empresa pela administração")
            flash("Não foi possível criar a empresa. Confira os dados e tente novamente.", "error")
            return redirect(url_for("admin.create_tenant"))
        flash(f"Empresa criada com sucesso! Acesso liberado por {days} dias. Envie ao cliente o link de acesso, e-mail e senha inicial com segurança.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/create_tenant.html")

@bp.route("/empresa/<int:tenant_id>", methods=["GET", "POST"])
@admin_required
def edit_tenant(tenant_id):
    tenant = db.get_or_404(Tenant, tenant_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        plan = request.form.get("subscription_plan", "Mensal").strip()
        expires = request.form.get("subscription_expires_at", "").strip()
        owner_name = request.form.get("owner_name", "").strip()
        owner_email = request.form.get("owner_email", "").strip().lower()
        whatsapp = re.sub(r"\D", "", request.form.get("whatsapp_number", ""))
        if len(whatsapp) in (10, 11):
            whatsapp = "55" + whatsapp
        owner = db.session.scalar(select(User).where(User.tenant_id == tenant.id, User.role == "owner").order_by(User.id.asc()))
        if not (10 <= len(whatsapp) <= 15):
            flash("Informe o WhatsApp da empresa com DDD e código do país quando necessário.", "error")
            return redirect(url_for("admin.edit_tenant", tenant_id=tenant.id))
        if not name or len(name) > 120 or not owner_name or len(owner_name) > 120 or "@" not in owner_email or len(owner_email) > 255:
            flash("Confira o nome da empresa, o nome do responsável e o e-mail.", "error")
            return redirect(url_for("admin.edit_tenant", tenant_id=tenant.id))
        if owner_email == os.getenv("PLATFORM_ADMIN_EMAIL", "").strip().lower():
            flash("Esse e-mail está reservado para a administração da plataforma.", "error")
            return redirect(url_for("admin.edit_tenant", tenant_id=tenant.id))
        if owner and db.session.scalar(select(User.id).where(User.email == owner_email, User.id != owner.id)) is not None:
            flash("Esse e-mail já está cadastrado em outra conta. Use outro e-mail.", "error")
            return redirect(url_for("admin.edit_tenant", tenant_id=tenant.id))
        tenant.name = name
        tenant.whatsapp_number = whatsapp
        tenant.subscription_plan = plan if plan in {"Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"} else "Mensal"
        if expires:
            try:
                tenant.subscription_expires_at = datetime.strptime(expires, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                flash("Data de vencimento inválida.", "error")
                return redirect(url_for("admin.edit_tenant", tenant_id=tenant.id))
        else:
            tenant.subscription_expires_at = None
        if owner:
            owner.name = owner_name
            owner.email = owner_email
        db.session.commit()
        flash("Dados da empresa atualizados.", "success")
        return redirect(url_for("admin.dashboard"))
    owner = db.session.scalar(select(User).where(User.tenant_id == tenant.id, User.role == "owner").order_by(User.id.asc()))
    expires = tenant.subscription_expires_at
    if expires and expires.tzinfo:
        expires = expires.astimezone(timezone.utc)
    return render_template("admin/edit_tenant.html", tenant=tenant, owner=owner, expiry_value=expires.strftime("%Y-%m-%d") if expires else "")

@bp.post("/empresa/<int:tenant_id>/bloquear")
@admin_required
def toggle_tenant(tenant_id):
    tenant = db.get_or_404(Tenant, tenant_id)
    tenant.is_active = not tenant.is_active
    db.session.commit()
    flash(f"Empresa {'desbloqueada' if tenant.is_active else 'bloqueada'} com sucesso.", "success")
    return redirect(url_for("admin.dashboard"))

@bp.post("/empresa/<int:tenant_id>/renovar")
@admin_required
def renew_tenant(tenant_id):
    tenant = db.get_or_404(Tenant, tenant_id)
    today = utc_now().date()
    current_expiry = tenant.subscription_expires_at
    if current_expiry and current_expiry.tzinfo is None:
        current_expiry = current_expiry.replace(tzinfo=timezone.utc)
    base_date = current_expiry.date() if current_expiry and current_expiry.date() > today else today
    duration = request.form.get("duration", "30")
    days = {"30": 30, "90": 90, "180": 180, "365": 365}.get(duration, 30)
    tenant.subscription_expires_at = datetime.combine(base_date + timedelta(days=days), datetime.min.time(), tzinfo=timezone.utc)
    tenant.is_active = True
    tenant.subscription_plan = {"30":"Mensal", "90":"Trimestral", "180":"Semestral", "365":"Anual"}[duration]
    db.session.commit()
    flash(f"Assinatura renovada por {days} dias.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/empresa/<int:tenant_id>/excluir")
@admin_required
def delete_tenant(tenant_id):
    tenant = db.get_or_404(Tenant, tenant_id)
    has_platform_admin = db.session.scalar(select(User.id).where(User.tenant_id == tenant.id, User.role == "platform_admin").limit(1)) is not None
    if tenant.slug == "borapedir-platform" or has_platform_admin:
        flash("A conta principal da plataforma não pode ser excluída.", "error")
        return redirect(url_for("admin.dashboard"))
    # Apaga primeiro os dados relacionados para funcionar também em bancos sem FK cascade ativo.
    from app.models import Product, Customer, Order, OrderItem
    order_ids = select(Order.id).where(Order.tenant_id == tenant.id)
    db.session.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
    db.session.query(Order).filter(Order.tenant_id == tenant.id).delete(synchronize_session=False)
    db.session.query(Product).filter(Product.tenant_id == tenant.id).delete(synchronize_session=False)
    db.session.query(Customer).filter(Customer.tenant_id == tenant.id).delete(synchronize_session=False)
    db.session.query(User).filter(User.tenant_id == tenant.id).delete(synchronize_session=False)
    db.session.delete(tenant)
    db.session.commit()
    flash("Empresa, acesso e dados relacionados excluídos.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/usuario/<int:user_id>/desbloquear")
@admin_required
def unlock_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.role == "platform_admin":
        flash("A conta principal não deve ser desbloqueada por este formulário.", "error")
    else:
        user.failed_login_attempts = 0
        user.login_locked = False
        db.session.commit()
        flash(f"Acesso de {user.email} desbloqueado.", "success")
    return redirect(url_for("admin.dashboard"))
