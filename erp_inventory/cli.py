"""Manage a small stock ledger from the terminal."""

import argparse
from pathlib import Path
import sqlite3

from .service import Inventory, rupees


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=Path('data/inventory.db'), help='SQLite file (default: data/inventory.db)')
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('add', help='Register a product with zero stock')
    add.add_argument('sku')
    add.add_argument('name')
    add.add_argument('--reorder', type=int, default=5)
    for command, description in [('receive', 'Record a purchase receipt'), ('sell', 'Record a sale')]:
        sub = commands.add_parser(command, help=description)
        sub.add_argument('sku')
        sub.add_argument('quantity', type=int)
        sub.add_argument('--price', required=True, help='Price per unit in INR, for example 125.50')
        sub.add_argument('--ref', default='', help='Supplier bill or sale reference')
    stock = commands.add_parser('stock', help='Show current stock')
    stock.add_argument('--low', action='store_true', help='Show items at or below their reorder level')
    commands.add_parser('history', help='Show purchases and sales')
    export = commands.add_parser('export', help='Export the movement ledger as CSV')
    export.add_argument('path', type=Path)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        inventory = Inventory(args.db)
        if args.command == 'add':
            sku = inventory.add_product(args.sku, args.name, args.reorder)
            print(f'Added {sku} with zero stock.')
        elif args.command in ('receive', 'sell'):
            kind = 'purchase' if args.command == 'receive' else 'sale'
            number = inventory.record(args.sku, kind, args.quantity, args.price, args.ref)
            print(f'Recorded {kind} #{number}: {args.quantity} units of {args.sku.upper()}.')
        elif args.command == 'stock':
            rows = inventory.stock(args.low)
            if not rows:
                print('No matching products.')
            for row in rows:
                flag = 'REORDER' if row['low_stock'] else 'OK'
                print(f"{row['sku']} | {row['name']} | stock: {row['quantity']} | reorder level: {row['reorder_level']} | {flag}")
        elif args.command == 'history':
            rows = inventory.history()
            if not rows:
                print('No stock movements yet.')
            for row in rows:
                total = rupees(row['quantity'] * row['unit_price_paise'])
                print(f"#{row['id']} | {row['created_at']} | {row['kind']} | {row['sku']} | {row['quantity']} units | INR {total} | {row['reference']}")
        elif args.command == 'export':
            print(f'Exported to {inventory.export(args.path).resolve()}')
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
