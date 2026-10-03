# Local Quran-only inheritance sources

`inheritance_rules.json` has 14 records citing only Quran 4:11, 4:12 and 4:176. The batch includes four spouse rules, three children rules, four parent rules and three full-sibling rules. References can be inspected at https://quran.com/4/11, https://quran.com/4/12 and https://quran.com/4/176. The JSON contains verse references without URLs.

Each record has `rule_id`, `applies_to`, `conditions`, `result`, `topic`, `rule` and nested `source` metadata. `backend/rag/source_validation.py` validates required fields, unique IDs, result fractions/weights, condition shapes and the allowed Quran references before retrieval.

The generic evaluator supports boolean/integer equality, integer `*_gte` and `*_lte` keys, and integer objects with `eq`, `min`, and `max`. The coverage gate independently rechecks rule conditions against factual case features. A relation appearing in `applies_to` alone is insufficient.

Spouse and daughter fractions are group shares. Joint children and joint full siblings use male weight 2 and female weight 1. The existing `sons_and_daughters_residue` ID is now `sons_and_daughters`.

Counts are factual and do not determine rulings. The configured `has_kalalah_context` requires no descendant and no father, not merely no child. This batch uses the requested daughter/sibling thresholds; it does not implement a complete interpretive or madhhab-specific engine.

The parent records describe specified fractions only. The father's additional residue is not implemented. The mother's third text retains the verse's context of parental inheritance; its requested conditions are a simplified retrieval filter, not a complete treatment of compound cases. Coverage checks matched rule availability, not the completeness of a final inheritance ruling.

Intentionally absent: father without child residue, full brother alone, maternal-sibling outcomes, extended-relative outcomes, blocking/precedence, awl and radd. Previously supported factual detection of extended descendant names remains available to avoid false kalalah classification; no inheritance rules for those relations are added.
