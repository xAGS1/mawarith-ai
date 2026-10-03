# Local inheritance sources

`inheritance_rules.json` contains four rules: wife with descendants (1/8), wife without descendants (1/4), mother with a child (1/6), and the residue shared by sons and daughters with male weight 2 and female weight 1. Sources are Quran 4:11 and 4:12. No URLs or additional fiqh rules are included.

Each object contains `rule_id`, `applies_to`, `conditions`, `result`, `topic`, `rule` and nested `source` metadata.

The shared retriever matches exact relation names and evaluates conditions in Python. Conditions support boolean/integer equality and integer objects with `eq`, `min` and `max` operators. All conditions must match; missing features and unsupported operators fail closed.

The features describe relatives and counts without inheritance rulings. The source set is incomplete for general cases, including the brother's share in the wife/full-brother retrieval test. The reasoner is instructed to avoid guessing when rules are insufficient. The shared verifier regenerates group shares from the per-person distribution and checks arithmetic totals, not legal correctness.
