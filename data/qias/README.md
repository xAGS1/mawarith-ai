# QIAS data

Place your local QIAS JSON files here.

Example:

```text
data/qias/qias2025_almawarith_part1.json
data/qias/qias2025_almawarith_part2.json
```

The starter does **not** redistribute the dataset.

Expected solved-case format:

```json
[
  {
    "id": "...",
    "question": "...",
    "output": {
      "heirs": [],
      "blocked": [],
      "shares": [],
      "awl_or_radd": "...",
      "post_tasil": {}
    }
  }
]
```
