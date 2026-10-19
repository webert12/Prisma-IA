from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


def utc_now():
    return datetime.now(timezone.utc)


class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    whatsapp_number = db.Column(db.String(30), nullable=True)
    business_type = db.Column(db.String(40), nullable=False, default="outros")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    subscription_plan = db.Column(db.String(40), nullable=False, default="Mensal")
    subscription_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    @property
    def subscription_status(self):
        if not self.is_active:
            return "Bloqueada"
        if self.subscription_expires_at is None:
            return "Sem prazo"
        expiry = self.subscription_expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return "Ativa" if expiry >= utc_now() else "Vencida"

    users = db.relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.slug}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="owner")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    login_locked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    tenant = db.relationship("Tenant", back_populates="users")
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "email", name="uq_user_email_per_tenant"),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active_user(self):
        return self.is_active and self.tenant.is_active


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    image_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    tenant = db.relationship("Tenant", backref=db.backref("products", cascade="all, delete-orphan"))


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    tenant = db.relationship("Tenant", backref=db.backref("customers", cascade="all, delete-orphan"))


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name = db.Column(db.String(160), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    delivery_type = db.Column(db.String(20), nullable=False, default="Retirada")
    payment_method = db.Column(db.String(30), nullable=False, default="Pix")
    delivery_address = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="Novo")
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    # Number shown to the business: resets for each tenant at 06:00 São Paulo time.
    daily_number = db.Column(db.Integer, nullable=True, index=True)
    operational_date = db.Column(db.Date, nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    tenant = db.relationship("Tenant", backref=db.backref("orders", cascade="all, delete-orphan"))
    customer = db.relationship("Customer")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = db.Column(db.String(160), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")


class BackupSnapshot(db.Model):
    """Weekly tenant snapshot stored in the configured database."""
    __tablename__ = "backup_snapshots"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = db.Column(db.Date, nullable=False)
    snapshot_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    __table_args__ = (db.UniqueConstraint("tenant_id", "week_start", name="uq_backup_tenant_week"),)
