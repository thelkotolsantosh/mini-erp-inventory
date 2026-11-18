import csv
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from erp_inventory.cli import main
from erp_inventory.service import Inventory, money_to_paise


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db = Path(self.folder.name) / 'inventory.db'
        self.inventory = Inventory(self.db)
        self.inventory.add_product('ROLLER-01', 'Window roller', 3)

    def test_purchase_and_sale_update_stock_and_persist(self):
        self.inventory.record('ROLLER-01', 'purchase', 10, '25.50', 'SUP-001')
        self.inventory.record('ROLLER-01', 'sale', 4, '32.75', 'SALE-001')
        reopened = Inventory(self.db)
        self.assertEqual(reopened.stock()[0]['quantity'], 6)
        self.assertEqual(len(reopened.history()), 2)

    def test_overselling_changes_neither_stock_nor_history(self):
        self.inventory.record('ROLLER-01', 'purchase', 2, '25')
        with self.assertRaisesRegex(ValueError, 'Insufficient stock'):
            self.inventory.record('ROLLER-01', 'sale', 3, '30')
        self.assertEqual(self.inventory.stock()[0]['quantity'], 2)
        self.assertEqual(len(self.inventory.history()), 1)

    def test_two_sales_cannot_use_the_same_stock(self):
        self.inventory.record('ROLLER-01', 'purchase', 10, '25')

        def sell():
            try:
                Inventory(self.db).record('ROLLER-01', 'sale', 7, '30')
                return True
            except ValueError:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: sell(), range(2)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.inventory.stock()[0]['quantity'], 3)

    def test_duplicate_sku_is_rejected_without_overwriting(self):
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.inventory.add_product('roller-01', 'Different name')
        self.assertEqual(self.inventory.stock()[0]['name'], 'Window roller')

    def test_unknown_product_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown product'):
            self.inventory.record('MISSING', 'purchase', 1, '10')

    def test_invalid_quantities_are_rejected(self):
        for quantity in [0, -1, 1.5, True, '2']:
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                self.inventory.record('ROLLER-01', 'purchase', quantity, '10')

    def test_money_is_exact_and_invalid_prices_are_rejected(self):
        self.assertEqual(money_to_paise('10.10'), 1010)
        for price in ['-1', 'NaN', 'Infinity', '1.005', 'bad']:
            with self.subTest(price=price), self.assertRaises(ValueError):
                money_to_paise(price)

    def test_reorder_boundary_includes_equal_quantity(self):
        self.inventory.record('ROLLER-01', 'purchase', 3, '25')
        self.assertEqual(len(self.inventory.stock(low_only=True)), 1)
        self.inventory.record('ROLLER-01', 'purchase', 1, '25')
        self.assertEqual(self.inventory.stock(low_only=True), [])

    def test_export_has_exact_totals_and_works_when_empty(self):
        path = Path(self.folder.name) / 'exports' / 'ledger.csv'
        self.inventory.export(path)
        with path.open(newline='') as handle:
            self.assertEqual(list(csv.DictReader(handle)), [])
        self.inventory.record('ROLLER-01', 'purchase', 3, '10.10', 'SUP-001')
        self.inventory.export(path)
        with path.open(newline='') as handle:
            row = next(csv.DictReader(handle))
        self.assertEqual(row['total_inr'], '30.30')
        self.assertEqual(row['reference'], 'SUP-001')

    def test_export_cannot_overwrite_database(self):
        with self.assertRaises(ValueError):
            self.inventory.export(self.db)
        self.assertEqual(self.inventory.stock()[0]['sku'], 'ROLLER-01')

    def test_cli_handles_a_complete_stock_flow(self):
        output = StringIO()
        with redirect_stdout(output):
            main(['--db', str(self.db), 'receive', 'ROLLER-01', '5', '--price', '10'])
            main(['--db', str(self.db), 'stock'])
        self.assertIn('stock: 5', output.getvalue())


if __name__ == '__main__':
    unittest.main()
