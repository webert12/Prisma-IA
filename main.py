import re
import os
import uuid
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import quote

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for, jsonify, Response, send_file, current_app
from flask_login import current_user, login_required
from sqlalchemy import select, func
from werkzeug.utils import secure_filename

from app import db
from app.models import Tenant, Product, Customer, Order, OrderItem

bp = Blueprint("main", __name__)


def owner_required():
    if not current_user.is_authenticated or current_user.role == "platform_admin":
        abort(403)
    if not current_user.tenant.is_active:
        abort(403)


def money(value):
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return Decimal("0.00")


def phone_digits(value):
    return re.sub(r"\D", "", value or "")


def operational_window(now_utc=None):
    """Return the current business-day start (06:00 America/Sao_Paulo) and its date.

    The business day runs from 06:00 until 05:59:59 the next morning.
    Historical orders remain stored; only the active queue and numbering reset.
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    local_tz = ZoneInfo("America/Sao_Paulo")
    now_local = now_utc.astimezone(local_tz)
    cycle_date = now_local.date() if now_local.hour >= 6 else now_local.date() - timedelta(days=1)
    start_local = datetime.combine(cycle_date, time(6, 0), tzinfo=local_tz)
    return start_local.astimezone(timezone.utc), cycle_date


def infer_category(name, category=""):
    """Use an explicit category when supplied; otherwise infer a sensible food category from the name."""
    if category and category.strip():
        return category.strip()[:100]
    text = (name or "").casefold()
    groups = [
        ("Refrigerantes e bebidas", ("refrigerante", "coca", "guarana", "guaraná", "fanta", "sprite", "pepsi", "soda", "suco", "água", "agua", "chá", "cha", "bebida", "lata", "cerveja", "energético", "energetico")),
        ("Salgados", ("salgado", "coxinha", "pastel", "empada", "esfiha", "kibe", "quibe", "enroladinho", "risole", "risole", "bolinha de queijo", "pão de queijo", "pao de queijo")),
        ("Hambúrgueres", ("burger", "hambúrguer", "hamburguer", "x-burger", "x-salada", "x-bacon", "x-tudo")),
        ("Pizzas", ("pizza",)),
        ("Doces e sobremesas", ("bolo", "brigadeiro", "doce", "pudim", "sorvete", "açaí", "acai", "brownie", "torta", "chocolate", "sobremesa", "milk-shake", "milk shake")),
        ("Porções", ("porção", "porcao", "batata frita", "fritas", "calabresa", "frango a passarinho", "anel de cebola")),
        ("Pratos e refeições", ("marmita", "prato", "refeição", "refeicao", "arroz", "feijão", "feijao", "lasanha", "macarrão", "macarrao", "strogonoff", "parmegiana")),
        ("Lanches", ("sanduíche", "sanduiche", "hot dog", "hot-dog", "cachorro-quente", "lanche", "misto quente", "bauru")),
    ]
    for label, keywords in groups:
        if any(word in text for word in keywords):
            return label
    return "Outros produtos"


@bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard" if current_user.role == "platform_admin" else "main.dashboard"))
    return render_template("index.html")


@bp.get("/painel")
@login_required
def dashboard():
    owner_required()
    tenant_id = current_user.tenant_id
    try:
        from app.backup_utils import automatic_daily_backup, automatic_weekly_database_backup
        automatic_daily_backup(tenant_id)
        automatic_weekly_database_backup(tenant_id)
    except Exception:
        current_app.logger.exception("Falha ao criar backup diário da empresa %s", tenant_id)
    product_count = db.session.scalar(select(func.count(Product.id)).where(Product.tenant_id == tenant_id)) or 0
    customer_count = db.session.scalar(select(func.count(Customer.id)).where(Customer.tenant_id == tenant_id)) or 0
    all_orders = db.session.scalars(
        select(Order).where(Order.tenant_id == tenant_id).order_by(Order.created_at.desc())
    ).all()

    # A fila operacional e a contagem reiniciam às 06:00, por empresa.
    cycle_start_utc, cycle_date = operational_window()
    active_orders = db.session.scalars(
        select(Order).where(
            Order.tenant_id == tenant_id,
            Order.created_at >= cycle_start_utc,
        ).order_by(Order.created_at.desc())
    ).all()
    order_count = len(active_orders)

    # Receita considera somente pedidos concluídos/entregues, não pedidos novos,
    # pendentes ou cancelados. Datas são calculadas no fuso de Brasília.
    local_tz = ZoneInfo("America/Sao_Paulo")
    now_local = datetime.now(timezone.utc).astimezone(local_tz)
    today = now_local.date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    delivered_statuses = {"Entregue", "Concluído"}
    sales = {"today": Decimal("0.00"), "week": Decimal("0.00"), "month": Decimal("0.00")}
    counts = {"today": 0, "week": 0, "month": 0}

    for order in all_orders:
        created = order.created_at
        if created is None:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        order_date = created.astimezone(local_tz).date()
        in_today = created >= cycle_start_utc
        in_week = week_start <= order_date <= today
        in_month = month_start <= order_date <= today
        if in_today: counts["today"] += 1
        if in_week: counts["week"] += 1
        if in_month: counts["month"] += 1
        if order.status in delivered_statuses:
            value = money(order.total)
            if in_today: sales["today"] += value
            if in_week: sales["week"] += value
            if in_month: sales["month"] += value

    return render_template(
        "dashboard.html", product_count=product_count, customer_count=customer_count,
        order_count=order_count, recent_orders=active_orders, sales=sales, period_counts=counts,
        today_label=now_local.strftime("%d/%m/%Y"), week_label=f"{week_start.strftime('%d/%m')} a {today.strftime('%d/%m')}",
        month_label=now_local.strftime("%m/%Y"),
    )


@bp.route("/configuracoes/loja", methods=["GET", "POST"])
@login_required
def store_settings():
    owner_required()
    tenant = current_user.tenant
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        whatsapp = phone_digits(request.form.get("whatsapp_number", ""))
        if len(whatsapp) in (10, 11):
            whatsapp = "55" + whatsapp
        if not name or len(name) > 120:
            flash("Informe um nome válido para a loja.", "error")
        elif whatsapp and not (10 <= len(whatsapp) <= 15):
            flash("Informe o WhatsApp com DDD e código do país quando necessário.", "error")
        else:
            tenant.name = name
            tenant.whatsapp_number = whatsapp or None
            db.session.commit()
            flash("Dados da loja salvos.", "success")
            return redirect(url_for("main.store_settings"))
    return render_template("store_settings.html", tenant=tenant)


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def save_product_image(upload):
    """Save an owner-uploaded image with a random name and a strict extension allowlist."""
    if not upload or not upload.filename:
        return None
    original = secure_filename(upload.filename)
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Use uma imagem JPG, PNG, WEBP ou GIF.")
    upload.stream.seek(0, os.SEEK_END)
    size = upload.stream.tell()
    upload.stream.seek(0)
    if size > 5 * 1024 * 1024:
        raise ValueError("A imagem deve ter no máximo 5 MB.")
    # Basic signature checks prevent uploading arbitrary files renamed as images.
    head = upload.stream.read(16)
    upload.stream.seek(0)
    valid = (
        (ext in {".jpg", ".jpeg"} and head.startswith(b"\xff\xd8\xff")) or
        (ext == ".png" and head.startswith(b"\x89PNG\r\n\x1a\n")) or
        (ext == ".gif" and head.startswith((b"GIF87a", b"GIF89a"))) or
        (ext == ".webp" and head.startswith(b"RIFF") and head[8:12] == b"WEBP")
    )
    if not valid:
        raise ValueError("O arquivo selecionado não parece ser uma imagem válida.")
    folder = Path(current_app.root_path) / "static" / "uploads" / "products"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    upload.save(folder / filename)
    return url_for("static", filename=f"uploads/products/{filename}")

def resolve_product_image(form_field="image_url", upload_field="image_file", existing=None):
    upload = request.files.get(upload_field)
    if upload and upload.filename:
        return save_product_image(upload)
    return request.form.get(form_field, "").strip()[:500] or existing or None


@bp.route("/produtos", methods=["GET", "POST"])
@login_required
def products():
    owner_required()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = infer_category(name, request.form.get("category", "").strip())
        image_url = request.form.get("image_url", "").strip()
        try:
            price = money(request.form.get("price", "0").replace(",", "."))
            if not name or len(name) > 160 or price < 0 or len(image_url) > 500:
                raise ValueError("Confira o nome, o preço e o endereço da imagem.")
            image_url = resolve_product_image() or image_url or None
            product = Product(tenant_id=current_user.tenant_id, name=name, description=description or None, category=category or None, image_url=image_url, price=price, is_available=True)
            db.session.add(product)
            db.session.commit()
            flash("Produto cadastrado com sucesso.", "success")
            return redirect(url_for("main.products"))
        except (ValueError, OSError) as exc:
            db.session.rollback()
            flash(str(exc) or "Confira os dados e a imagem selecionada.", "error")
    products_list = db.session.scalars(select(Product).where(Product.tenant_id == current_user.tenant_id).order_by(Product.created_at.desc())).all()
    return render_template("products.html", products=products_list)


@bp.post("/produtos/<int:product_id>/editar")
@login_required
def edit_product(product_id):
    owner_required()
    product = db.session.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == current_user.tenant_id))
    if product is None: abort(404)
    name = request.form.get("name", "").strip()
    try: price = money(request.form.get("price", "0").replace(",", "."))
    except Exception: price = Decimal("-1")
    if not name or price < 0:
        flash("Informe nome e preço válido.", "error")
    else:
        product.name = name[:160]
        product.price = price
        product.category = infer_category(name, request.form.get("category", "").strip())
        product.description = request.form.get("description", "").strip() or None
        try:
            product.image_url = resolve_product_image(existing=product.image_url)
            product.is_available = request.form.get("is_available") == "on"
            db.session.commit()
            flash("Produto atualizado.", "success")
        except (ValueError, OSError) as exc:
            db.session.rollback()
            flash(str(exc) or "Não foi possível salvar a imagem.", "error")
    return redirect(url_for("main.products"))


@bp.post("/produtos/<int:product_id>/excluir")
@login_required
def delete_product(product_id):
    owner_required()
    product = db.session.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == current_user.tenant_id))
    if product is None: abort(404)
    db.session.delete(product)
    db.session.commit()
    flash("Produto excluído.", "success")
    return redirect(url_for("main.products"))


@bp.route("/clientes", methods=["GET", "POST"])
@login_required
def customers():
    owner_required()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = phone_digits(request.form.get("phone", ""))
        email = request.form.get("email", "").strip().lower()
        notes = request.form.get("notes", "").strip()
        if not name:
            flash("Informe o nome do cliente.", "error")
        else:
            customer = Customer(tenant_id=current_user.tenant_id, name=name[:160], phone=phone or None, email=email[:255] or None, notes=notes or None)
            db.session.add(customer); db.session.commit()
            flash("Cliente cadastrado.", "success")
            return redirect(url_for("main.customers"))
    customers_list = db.session.scalars(select(Customer).where(Customer.tenant_id == current_user.tenant_id).order_by(Customer.created_at.desc())).all()
    return render_template("customers.html", customers=customers_list)


@bp.post("/clientes/<int:customer_id>/excluir")
@login_required
def delete_customer(customer_id):
    owner_required()
    customer = db.session.scalar(select(Customer).where(Customer.id == customer_id, Customer.tenant_id == current_user.tenant_id))
    if customer is None: abort(404)
    db.session.delete(customer); db.session.commit()
    flash("Cliente excluído.", "success")
    return redirect(url_for("main.customers"))


@bp.get("/pedidos")
@login_required
def orders():
    owner_required()
    cycle_start_utc, _cycle_date = operational_window()
    orders_list = db.session.scalars(
        select(Order).where(
            Order.tenant_id == current_user.tenant_id,
            Order.created_at >= cycle_start_utc,
        ).order_by(Order.created_at.desc())
    ).all()
    return render_template("orders.html", orders=orders_list)


@bp.post("/pedidos/<int:order_id>/status")
@login_required
def update_order_status(order_id):
    owner_required()
    order = db.session.scalar(select(Order).where(Order.id == order_id, Order.tenant_id == current_user.tenant_id))
    if order is None: abort(404)
    status = request.form.get("status", "Novo")
    # New workflow: Novo -> Pendente (owner confirms) -> Entregue (order sent/delivered).
    allowed = {"Pendente", "Entregue", "Cancelado"}
    if status not in allowed:
        abort(400)
    if order.status in {"Entregue", "Cancelado"}:
        flash("Este pedido já foi finalizado e não pode ser alterado.", "error")
        return redirect(url_for("main.orders"))
    if status == "Entregue" and order.status != "Pendente":
        abort(400)
    order.status = status
    # Remove the customer's precise address/location as soon as the order is marked delivered.
    if status == "Entregue":
        order.delivery_address = None
    db.session.commit()
    flash("Pedido confirmado. Use o botão de WhatsApp no cartão para avisar o cliente." if status == "Pendente" else ("Pedido marcado como entregue. A localização do cliente foi removida." if status == "Entregue" else "Pedido cancelado."), "success")
    return redirect(url_for("main.orders"))


@bp.get("/pedidos/<int:order_id>/whatsapp-confirmacao")
@login_required
def whatsapp_order_confirmation(order_id):
    """Open a prefilled WhatsApp reply for the owner to send to the customer."""
    owner_required()
    order = db.session.scalar(select(Order).where(
        Order.id == order_id,
        Order.tenant_id == current_user.tenant_id,
    ))
    if order is None:
        abort(404)
    if order.status != "Pendente":
        flash("A mensagem de confirmação só está disponível após confirmar o pedido.", "error")
        return redirect(url_for("main.orders"))
    phone = phone_digits(order.customer_phone)
    if len(phone) in (10, 11):
        phone = "55" + phone
    if not (10 <= len(phone) <= 15):
        flash("Este pedido não tem um telefone válido para WhatsApp.", "error")
        return redirect(url_for("main.orders"))
    message = (
        f"Olá, {order.customer_name}! Obrigado pelo seu pedido na {order.tenant.name}. "
        f"Confirmamos que recebemos seu pedido #{order.daily_number or order.id}, no valor de R$ {order.total:.2f}. "
        "Já estamos preparando tudo. Agradecemos pela preferência!"
    )
    return redirect(f"https://wa.me/{phone}?text={quote(message)}")


@bp.get("/pedidos/notificacoes")
@login_required
def order_notifications():
    """Small polling endpoint for in-app new-order alerts; scoped to the signed-in tenant."""
    owner_required()
    tenant_id = current_user.tenant_id
    cycle_start_utc, _cycle_date = operational_window()
    new_count = db.session.scalar(
        select(func.count(Order.id)).where(
            Order.tenant_id == tenant_id, Order.status == "Novo", Order.created_at >= cycle_start_utc
        )
    ) or 0
    newest = db.session.scalar(
        select(func.max(Order.id)).where(
            Order.tenant_id == tenant_id, Order.status == "Novo", Order.created_at >= cycle_start_utc
        )
    ) or 0
    return jsonify({"new_count": int(new_count), "newest_id": int(newest)})


@bp.get("/seguranca-backups")
@login_required
def security_backups():
    owner_required()
    return render_template("security_backups.html", tenant=current_user.tenant)


@bp.get("/backup/baixar.json")
@login_required
def download_backup():
    owner_required()
    import json
    from datetime import datetime, timezone
    from app.backup_utils import build_tenant_backup
    data = build_tenant_backup(current_user.tenant_id)
    filename = f"backup_{current_user.tenant.slug}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    response = Response(json.dumps(data, ensure_ascii=False, indent=2), mimetype="application/json")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/loja/<slug>")
def public_store(slug):
    tenant = db.session.scalar(select(Tenant).where(Tenant.slug == slug, Tenant.is_active.is_(True)))
    if tenant is None: abort(404)
    if tenant.subscription_expires_at:
        expiry = tenant.subscription_expires_at
        from datetime import timezone
        if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc)
        from app.models import utc_now
        if expiry < utc_now(): abort(404)
    products_list = db.session.scalars(select(Product).where(Product.tenant_id == tenant.id, Product.is_available.is_(True)).order_by(Product.category, Product.name)).all()
    # Group catalog items by category for the public ordering page.
    grouped_products = {}
    for product in products_list:
        category = infer_category(product.name, product.category or "")
        grouped_products.setdefault(category, []).append(product)
    return render_template("public_store.html", tenant=tenant, products=products_list, grouped_products=grouped_products)


@bp.post("/loja/<slug>/pedido")
def create_public_order(slug):
    tenant = db.session.scalar(select(Tenant).where(Tenant.slug == slug, Tenant.is_active.is_(True)))
    if tenant is None or not tenant.whatsapp_number:
        flash("Esta loja ainda não configurou o WhatsApp para pedidos.", "error")
        return redirect(url_for("main.public_store", slug=slug))
    from datetime import timezone
    if tenant.subscription_expires_at:
        expiry = tenant.subscription_expires_at
        if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc)
        from app.models import utc_now
        if expiry < utc_now(): abort(404)
    customer_name = request.form.get("customer_name", "").strip()
    customer_phone = phone_digits(request.form.get("customer_phone", ""))
    notes = request.form.get("notes", "").strip()
    delivery_type = request.form.get("delivery_type", "Retirada")
    payment_method = request.form.get("payment_method", "Pix")
    delivery_address = request.form.get("delivery_address", "").strip()
    if delivery_type not in {"Retirada", "Delivery"}:
        delivery_type = "Retirada"
    if payment_method not in {"Pix", "Cartão", "Dinheiro"}:
        payment_method = "Pix"
    if delivery_type == "Delivery" and not delivery_address:
        flash("Informe o endereço de entrega ou a localização para delivery.", "error")
        return redirect(url_for("main.public_store", slug=slug))
    if not customer_name:
        flash("Informe seu nome para concluir o pedido.", "error")
        return redirect(url_for("main.public_store", slug=slug))
    raw_ids = request.form.getlist("product_id")
    quantities = request.form.getlist("quantity")
    wanted = {}
    for raw_id, raw_qty in zip(raw_ids, quantities):
        try: pid, qty = int(raw_id), int(raw_qty)
        except (ValueError, TypeError): continue
        if qty > 0: wanted[pid] = min(qty, 99)
    if not wanted:
        flash("Escolha pelo menos um produto.", "error")
        return redirect(url_for("main.public_store", slug=slug))
    valid_products = db.session.scalars(select(Product).where(Product.tenant_id == tenant.id, Product.id.in_(wanted.keys()), Product.is_available.is_(True))).all()
    if len(valid_products) != len(wanted):
        flash("Um dos produtos selecionados não está disponível. Atualize a página e tente novamente.", "error")
        return redirect(url_for("main.public_store", slug=slug))
    customer = None
    if customer_phone:
        customer = db.session.scalar(select(Customer).where(Customer.tenant_id == tenant.id, Customer.phone == customer_phone))
    if customer is None:
        customer = Customer(tenant_id=tenant.id, name=customer_name, phone=customer_phone or None)
        db.session.add(customer); db.session.flush()
    else:
        customer.name = customer_name
    cycle_start_utc, cycle_date = operational_window()
    last_number = db.session.scalar(
        select(func.max(Order.daily_number)).where(
            Order.tenant_id == tenant.id, Order.operational_date == cycle_date
        )
    ) or 0
    order = Order(
        tenant_id=tenant.id, customer_id=customer.id, customer_name=customer_name,
        customer_phone=customer_phone or None, notes=notes or None,
        delivery_type=delivery_type, payment_method=payment_method,
        delivery_address=delivery_address or None, status="Novo", total=Decimal("0.00"),
        daily_number=int(last_number) + 1, operational_date=cycle_date,
    )
    db.session.add(order); db.session.flush()
    total = Decimal("0.00")
    # Saudação neutra, sem inserir o nome do estabelecimento.
    lines = ["Olá, quero fazer este pedido:"]
    for product in valid_products:
        qty = wanted[product.id]
        line_total = money(product.price) * qty
        total += line_total
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name, unit_price=money(product.price), quantity=qty, line_total=line_total))
        lines.append(f"• {product.name} x{qty} — R$ {line_total:.2f}".replace('.', ','))
    order.total = total
    lines.append(f"TOTAL: R$ {total:.2f}".replace('.', ','))
    lines.append(f"Cliente: {customer_name}")
    if customer_phone: lines.append(f"Telefone: {customer_phone}")
    lines.append(f"Entrega: {'Delivery' if delivery_type == 'Delivery' else 'Retirada no estabelecimento'}")
    if delivery_type == "Delivery" and delivery_address:
        if delivery_address.startswith(("https://", "http://")):
            map_link = delivery_address
        else:
            map_link = "https://www.google.com/maps/search/?api=1&query=" + quote(delivery_address)
        lines.append(f"📍 Localização do cliente (toque para abrir no mapa): {map_link}")
    lines.append(f"Forma de pagamento: {payment_method}")
    if notes: lines.append(f"Observações: {notes}")
    db.session.commit()
    wa_message = quote("\n".join(lines))
    wa_number = phone_digits(tenant.whatsapp_number)
    return render_template("order_success.html", tenant=tenant, order=order, whatsapp_url=f"https://wa.me/{wa_number}?text={wa_message}")
