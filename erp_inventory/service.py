"""Store products and stock movements in SQLite."""

import csv
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sqlite3

MAX_INTEGER = 2**63 - 1


def money_to_paise(value):
    """Accept rupees with up to two decimal places, without float rounding."""
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0:
            raise ValueError("Price must be a finite, nonnegative amount.")
        paise = amount * 100
        if paise != paise.to_integral_value() or paise > MAX_INTEGER:
            raise ValueError("Price must have at most two decimal places and fit in the ledger.")
        return int(paise)
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid price, for example 125.50.") from None


def rupees(paise):
    return f"{Decimal(paise) / 100:.2f}"


def validate_quantity(value, allow_zero=False):
    minimum = 0 if allow_zero else 1
    if type(value) is not int or not minimum <= value <= MAX_INTEGER:
        raise ValueError(f"Quantity must be a whole number between {minimum} and {MAX_INTEGER}.")
    return value


class Inventory:
    def __init__(self, database):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    sku TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    reorder_level INTEGER NOT NULL CHECK(reorder_level >= 0)
                );
                CREATE TABLE IF NOT EXISTS movements (
                    id INTEGER PRIMARY KEY,
                    sku TEXT NOT NULL REFERENCES products(sku),
                    kind TEXT NOT NULL CHECK(kind IN ('purchase', 'sale')),
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    unit_price_paise INTEGER NOT NULL CHECK(unit_price_paise >= 0),
                    reference TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                );
                CREATE INDEX IF NOT EXISTS movements_sku ON movements(sku);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def normalize_sku(sku):
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("SKU cannot be blank.")
        sku = sku.strip().upper()
        if len(sku) > 40 or not all(c.isascii() and (c.isalnum() or c in '-_') for c in sku):
            raise ValueError("Use up to 40 letters, digits, hyphens, or underscores for the SKU.")
        return sku

    def add_product(self, sku, name, reorder_level=5):
        sku = self.normalize_sku(sku)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Product name cannot be blank.")
        validate_quantity(reorder_level, allow_zero=True)
        try:
            with self.connection() as db:
                db.execute("INSERT INTO products VALUES (?, ?, ?)", (sku, name.strip(), reorder_level))
        except sqlite3.IntegrityError:
            raise ValueError(f"Product {sku} already exists.") from None
        return sku

    def record(self, sku, kind, quantity, unit_price, reference=''):
        sku = self.normalize_sku(sku)
        if kind not in ('purchase', 'sale'):
            raise ValueError("Movement must be a purchase or sale.")
        validate_quantity(quantity)
        price = money_to_paise(unit_price)
        if price * quantity > MAX_INTEGER:
            raise ValueError("The line total is too large for the ledger.")
        if not isinstance(reference, str):
            raise ValueError("Reference must be text.")
        with self.connection() as db:
            # Lock before reading stock so two sales cannot spend the same units.
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM products WHERE sku = ?", (sku,)).fetchone():
                raise ValueError(f"Unknown product: {sku}")
            rows = db.execute("SELECT kind, quantity FROM movements WHERE sku = ?", (sku,))
            balance = sum(row['quantity'] if row['kind'] == 'purchase' else -row['quantity'] for row in rows)
            if kind == 'sale' and quantity > balance:
                raise ValueError(f"Insufficient stock: {sku} has {balance} units available.")
            if kind == 'purchase' and balance + quantity > MAX_INTEGER:
                raise ValueError("The stock balance is too large for the ledger.")
            cursor = db.execute(
                "INSERT INTO movements (sku, kind, quantity, unit_price_paise, reference) VALUES (?, ?, ?, ?, ?)",
                (sku, kind, quantity, price, reference.strip()),
            )
            return cursor.lastrowid

    def stock(self, low_only=False):
        with self.connection() as db:
            products = db.execute("SELECT * FROM products ORDER BY sku").fetchall()
            balances = {row['sku']: 0 for row in products}
            for row in db.execute("SELECT sku, kind, quantity FROM movements"):
                balances[row['sku']] += row['quantity'] if row['kind'] == 'purchase' else -row['quantity']
        result = []
        for product in products:
            row = dict(product)
            row['quantity'] = balances[row['sku']]
            row['low_stock'] = row['quantity'] <= row['reorder_level']
            if not low_only or row['low_stock']:
                result.append(row)
        return result

    def history(self):
        with self.connection() as db:
            rows = db.execute("SELECT * FROM movements ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def export(self, path):
        path = Path(path)
        if path.resolve() == self.database.resolve():
            raise ValueError("Export path must differ from the database path.")
        path.parent.mkdir(parents=True, exist_ok=True)
        columns = ['id', 'created_at', 'sku', 'kind', 'quantity', 'unit_price_inr', 'total_inr', 'reference']
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for movement in self.history():
                writer.writerow({
                    'id': movement['id'], 'created_at': movement['created_at'],
                    'sku': movement['sku'], 'kind': movement['kind'], 'quantity': movement['quantity'],
                    'unit_price_inr': rupees(movement['unit_price_paise']),
                    'total_inr': rupees(movement['quantity'] * movement['unit_price_paise']),
                    'reference': movement['reference'],
                })
        return path
