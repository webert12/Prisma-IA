"""Tenant-scoped backups and accounting exports for BoraPedir."""
import json
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from app.models import Tenant, User, Product, Customer, Order, OrderItem, BackupSnapshot
from app import db

LOCAL_TZ = ZoneInfo("America/Sao_Paulo")


def _value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _rows(model, tenant_id, omit_fields=()):
    rows = db.session.query(model).filter(model.tenant_id == tenant_id).all()
    result = []
    for row in rows:
        item = {}
        for column in model.__table__.columns:
            if column.name in omit_fields:
                continue
            item[column.name] = _value(getattr(row, column.name))
        result.append(item)
    return result


def build_tenant_backup(tenant_id):
    tenant = db.session.get(Tenant, tenant_id)
    if tenant is None:
        raise ValueError("Empresa não encontrada")
    orders = _rows(Order, tenant_id)
    order_ids = [row["id"] for row in orders]
    items = []
    if order_ids:
        for row in db.session.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all():
            items.append({column.name: _value(getattr(row, column.name)) for column in OrderItem.__table__.columns})
    users = []
    for user in db.session.query(User).filter(User.tenant_id == tenant_id).all():
        users.append({"id": user.id, "name": user.name, "email": user.email, "role": user.role,
                      "is_active": user.is_active, "created_at": _value(user.created_at)})
    return {
        "format": "BoraPedir tenant backup v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug,
                    "whatsapp_number": tenant.whatsapp_number, "business_type": tenant.business_type,
                    "created_at": _value(tenant.created_at)},
        "users_without_passwords": users,
        "products": _rows(Product, tenant_id),
        "customers": _rows(Customer, tenant_id),
        "orders": orders,
        "order_items": items,
        "privacy_note": "Arquivo contém dados comerciais e pessoais. Guarde em local protegido. Senhas não são exportadas."
    }


def automatic_daily_backup(tenant_id):
    """Create one daily snapshot per tenant; BACKUP_DIR should point to persistent storage."""
    root = Path(os.getenv("BACKUP_DIR", str(Path(__file__).resolve().parent.parent / "instance" / "backups")))
    root.mkdir(parents=True, exist_ok=True)
    day = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    path = root / f"tenant-{tenant_id}-daily-{day}.json"
    if path.exists():
        return path
    data = build_tenant_backup(tenant_id)
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    # Keep at most 30 daily snapshots per tenant on the configured storage.
    backups = sorted(root.glob(f"tenant-{tenant_id}-daily-*.json"), key=lambda item: item.name, reverse=True)
    for old_path in backups[30:]:
        try:
            old_path.unlink()
        except OSError:
            pass
    return path


def automatic_weekly_database_backup(tenant_id):
    """Persist one tenant-scoped snapshot per Brasília week in the app database.

    This is useful for accidental edits/deletions, but is not a substitute for an
    independent database backup if the database itself becomes unavailable.
    It runs when an owner opens the dashboard after a new week begins.
    """
    now_local = datetime.now(LOCAL_TZ)
    week_start = now_local.date() - timedelta(days=now_local.weekday())
    existing = db.session.query(BackupSnapshot).filter_by(tenant_id=tenant_id, week_start=week_start).first()
    if existing:
        return existing
    payload = json.dumps(build_tenant_backup(tenant_id), ensure_ascii=False, separators=(",", ":"))
    snapshot = BackupSnapshot(tenant_id=tenant_id, week_start=week_start, snapshot_json=payload)
    db.session.add(snapshot)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Concurrent dashboard requests can race on the unique tenant/week key.
        existing = db.session.query(BackupSnapshot).filter_by(tenant_id=tenant_id, week_start=week_start).first()
        if existing:
            return existing
        raise
    # Keep 12 weekly snapshots per tenant in the database.
    old = (db.session.query(BackupSnapshot).filter(BackupSnapshot.tenant_id == tenant_id)
           .order_by(BackupSnapshot.week_start.desc()).offset(12).all())
    for item in old:
        db.session.delete(item)
    if old:
        db.session.commit()
    return snapshot
