"""Run a stock example without changing the normal inventory database."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from erp_inventory.cli import main


def demo():
    with TemporaryDirectory() as folder:
        database = str(Path(folder) / 'demo.db')
        commands = [
            ['add', 'ROLLER-01', 'Window roller', '--reorder', '3'],
            ['add', 'HANDLE-01', 'Window handle', '--reorder', '5'],
            ['receive', 'ROLLER-01', '10', '--price', '25.50', '--ref', 'SUP-001'],
            ['receive', 'HANDLE-01', '4', '--price', '80.00', '--ref', 'SUP-002'],
            ['sell', 'ROLLER-01', '4', '--price', '32.75', '--ref', 'SALE-001'],
            ['stock'], ['stock', '--low'], ['history'],
        ]
        for command in commands:
            print('\n> ' + ' '.join(command))
            main(['--db', database, *command])


if __name__ == '__main__':
    demo()
