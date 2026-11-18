# Mini ERP Inventory

A small stock-management program for a shop or workshop. Register products, receive purchases, record sales, check low stock, and export the ledger to CSV.

The sample products are window rollers, handles, and screws. You can use your own product names and SKUs.

## Quick start

Install Python 3.11 or newer. Download or clone this repository and open a terminal in its folder.

```bash
python -m pip install -r requirements.txt
python examples/demo.py
```

On Windows, use `py` instead of `python` if needed. `requirements.txt` contains no external packages. The demo uses a temporary database and removes it when it finishes.

## Use the program

```bash
python app.py add ROLLER-01 "Window roller" --reorder 3
python app.py receive ROLLER-01 10 --price 25.50 --ref SUP-001
python app.py sell ROLLER-01 4 --price 32.75 --ref SALE-001
python app.py stock
python app.py stock --low
python app.py history
python app.py export exports/ledger.csv
```

After these commands, ROLLER-01 has 6 units in stock. The purchase total is INR 255.00 and the sale total is INR 131.00. These are movement totals, not a profit calculation.

An attempted sale of 7 more units fails with `Insufficient stock`. The failed sale does not change the quantity or ledger.

## Database location

The normal database is `data/inventory.db`, relative to the folder where you run the command. The program creates the folder and tables automatically.

Use `--db` **before the subcommand** to select another database:

```bash
python app.py --db data/workshop.db stock
```

Keep using the same database path for the same inventory. A new path creates a separate empty ledger. To back up your inventory, close the program and copy its database file.

## Commands

| Command | What it does |
|---|---|
| `add SKU "Name" --reorder N` | Register a product with zero stock |
| `receive SKU QTY --price PRICE --ref REF` | Record a purchase receipt |
| `sell SKU QTY --price PRICE --ref REF` | Record a sale if enough units are available |
| `stock` | Show all product balances |
| `stock --low` | Show balances at or below the reorder level |
| `history` | Show purchases and sales in entry order |
| `export PATH` | Write the full movement ledger to CSV |

`--ref` is optional. Prices are per unit in INR. Quantities must be positive whole numbers. Reorder levels may be zero. Prices may be zero and must have no more than two decimal places. Use `python app.py --help` or `python app.py sell --help` for command details.

## How stock is calculated

Stock on hand = units received − units sold.

Every purchase and sale is stored as a separate movement. The program calculates balances from that history. It checks the balance and writes a sale inside one database transaction, so two simultaneous sales cannot use the same available units.

Money is stored as integer paise and parsed with Decimal. For example, INR 25.50 is stored as 2550 paise. UTC timestamps are recorded for stock movements.

## Files

| File | Purpose |
|---|---|
| `app.py` | Short launcher for a source checkout |
| `erp_inventory/service.py` | Validation, stock ledger, SQLite storage, CSV export |
| `erp_inventory/cli.py` | Terminal commands and output |
| `erp_inventory/__init__.py` | Package version |
| `erp_inventory/__main__.py` | Support for `python -m erp_inventory` |
| `requirements.txt` | Runtime dependency declaration; no external packages |
| `pyproject.toml` | Optional package installation and `erp-stock` command |
| `tests/test_inventory.py` | Stock, money, persistence, concurrency, export, and CLI tests |
| `examples/demo.py` | A complete example using a temporary database |
| `data/sample_products.csv` | Fictional product examples; reference data, not an automatic import |
| `.github/workflows/tests.yml` | Run tests and demo on Linux/Windows with Python 3.11/3.12 |
| `.gitignore` | Exclude databases, exports, environments, and build files |
| `FAQ.md` | 25 questions and answers |
| `CONTRIBUTING.md` | How to check and submit changes |
| `CHANGELOG.md` | Release notes |
| `LICENSE` | MIT license |
| `README.md` | Setup, usage, and scope |

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests use temporary databases. They do not change the normal inventory file.

## Optional installation

Running `app.py` does not require installation. If you prefer a terminal command:

```bash
python -m pip install -e .
erp-stock stock
```

This step uses setuptools as a build tool. It adds no application runtime dependencies.

## Scope

This is a learning project for one inventory workflow. It does not include a web interface, login, GST invoices, payments, accounting entries, purchase-order approval, returns, or multi-warehouse stock. It does not connect to SAP or Oracle Fusion.

Each `receive` or `sell` command records a new event. Reusing a reference does not prevent duplicate entry. Entries cannot be edited or deleted through this version. Review the SKU, quantity, and price before recording a movement.

CSV export replaces an existing file at the chosen export path. Review untrusted text before opening exported CSVs in a spreadsheet. The database and exports are excluded from Git to keep operating records out of the repository.

See [FAQ.md](FAQ.md) for details and [LICENSE](LICENSE) for usage terms.
