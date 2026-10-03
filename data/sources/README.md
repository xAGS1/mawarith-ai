# Local inheritance sources

`inheritance_rules.json` contains only the three rules requested for the initial wife, mother, two sons and one daughter case, with Quran references 4:11 and 4:12. No URLs or additional fiqh rules are included.

The model-independent retriever matches exact relation names and returns complete rule objects, including source metadata. Retrieved rules are candidates; the reasoner must respect the conditions stated in each rule.

This small source set does not support general QIAS inheritance cases. The reasoner is instructed to return empty distributions when sources are insufficient; the fraction verifier then reports an inconsistent distribution. It checks arithmetic totals, not the legal correctness or completeness of a ruling.
