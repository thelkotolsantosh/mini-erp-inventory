# Contributing

Use Python 3.11 or newer. Keep changes focused on a clear problem and describe the resulting behavior in plain language.

Before submitting a change, run:

```bash
python -m unittest discover -s tests -v
python examples/demo.py
```

Add a regression test when fixing a calculation, validation, or stock-update bug. Use temporary databases in tests. Do not commit operating databases, exports, customer records, or credentials.
