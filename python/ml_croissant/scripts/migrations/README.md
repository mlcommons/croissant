# Migrations

To keep track of migrations, you can commit them in `pasts/`.

A good migration:
- has a formatted name `YYYYmmddHHmm.py`,
- declares a function `up` that takes a compacted JSON-LD and returns a compacted JSON-LD.

Then run:

```bash
python scripts/migrations/migrate.py --migration 202307171508
```
