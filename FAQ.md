# Frequently asked questions

1. **What does this program do?** It tracks products, stock received, stock sold, low-stock items, and a movement history.
2. **Why is this an ERP project?** Inventory is one part of an ERP system. This project implements that single workflow on a small scale.
3. **Does it connect to SAP or Oracle Fusion?** No. It runs locally and stores its own inventory records.
4. **Which Python version should I use?** Python 3.11 or newer. The automated checks cover Python 3.11 and 3.12 on Linux and Windows.
5. **What packages must I install?** None for normal use. SQLite, Decimal, argparse, CSV, and unittest are included with Python.
6. **Why include requirements.txt if it is empty of packages?** It states the dependency choice and lets the usual `pip install -r requirements.txt` setup command work.
7. **What is a SKU?** A unique product code, such as ROLLER-01. The program normalizes SKUs to uppercase.
8. **How do I add opening stock?** Add the product, then use `receive` with a reference such as OPENING-COUNT. Adding a product alone gives it zero stock.
9. **How is stock calculated?** Units received minus units sold, calculated from the movement ledger.
10. **Can a sale make stock negative?** No. The program rejects a sale when its quantity exceeds available stock.
11. **What happens if two sales run at once?** A write transaction starts before the balance check. One sale completes first; the next checks the updated balance.
12. **Why store prices as paise?** Integer paise avoids binary floating-point rounding for two-decimal INR amounts.
13. **Can I enter 10.005 as a price?** No. Prices must have at most two decimal places. The program rejects extra fractions rather than rounding them silently.
14. **Are decimal quantities supported?** No. This version counts whole items. It is not suitable for measurements such as square feet or kilograms without changes.
15. **When is an item marked for reorder?** When its quantity is less than or equal to its configured reorder level.
16. **Where is my database?** By default, at `data/inventory.db` under the folder where you run the program. Use `--db` before the command to choose another path.
17. **How do I back up the records?** Close the program and copy the SQLite database file to a safe location.
18. **Can I import sample_products.csv?** There is no import command in this version. The CSV shows example values; use `add` to register products or run the demo.
19. **What does the CSV export contain?** Movement ID, UTC timestamp, SKU, purchase/sale type, quantity, unit price in INR, line total in INR, and reference.
20. **Does it calculate profit or stock valuation?** No. Purchase and sale line totals are recorded separately. There is no FIFO, weighted-average cost, or profit calculation.
21. **Does it handle GST or invoices?** No. It records stock movements and references. It does not issue tax invoices or create accounting entries.
22. **Can I correct or delete a movement?** This version has no edit, delete, return, or stock-adjustment command. Check entries before recording them and keep backups.
23. **Will using the same reference stop duplicate entries?** No. Each command creates a new movement even when the reference repeats. Reference text is a note, not an idempotency key.
24. **How do I run the tests?** Run `python -m unittest discover -s tests -v` from the repository root. The tests use temporary databases.
25. **What could be added next?** Supplier and customer records, validated CSV import, returns, stock adjustments, purchase orders, and a small web interface are possible extensions.
