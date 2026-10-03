"""Model-independent arithmetic verification based on per-individual shares."""

from fractions import Fraction
from functools import reduce
from math import gcd


def lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


def lcm_many(numbers):
    return reduce(lcm, numbers, 1)


def verify_distribution(distribution):
    fractions = []
    for item in distribution:
        count = item["count"]
        if type(count) is not int or count < 1:
            raise ValueError("Distribution counts must be positive integers")
        fraction = Fraction(item["per_head_shares"])
        if fraction < 0 or fraction > 1:
            raise ValueError("Per-head shares must be between zero and one")
        fractions.append(fraction)

    total_shares = lcm_many(f.denominator for f in fractions) if fractions else 0
    total_fraction = sum(
        (fraction * item["count"] for item, fraction in zip(distribution, fractions)),
        Fraction(0, 1),
    )
    normalized = []
    shares = []
    for item, fraction in zip(distribution, fractions):
        numerator = fraction.numerator * (total_shares // fraction.denominator)
        normalized.append({
            "heir": item["heir"],
            "count": item["count"],
            "per_head_shares": f"{numerator}/{total_shares}",
            "per_head_percent": round(float(fraction) * 100, 2),
        })
        shares.append({
            "heir": item["heir"],
            "count": item["count"],
            "fraction": str(fraction * item["count"]),
        })

    return {
        "total_shares": total_shares,
        "total_fraction": str(total_fraction),
        "is_consistent": bool(distribution) and total_fraction == 1,
        "distribution": normalized,
        "shares": shares,
    }


def verify_and_normalize(result: dict) -> dict:
    """Replace model arithmetic with exact fractions without changing the input.

    Consistency checks the estate total, not the legal validity of a ruling.
    An empty distribution is explicitly inconsistent.
    """
    verification = verify_distribution(result.get("post_tasil", {}).get("distribution", []))
    normalized = dict(result)
    normalized["shares"] = verification["shares"]
    normalized["post_tasil"] = {
        **result.get("post_tasil", {}),
        "total_shares": verification["total_shares"],
        "distribution": verification["distribution"],
    }
    normalized["verification"] = {
        "total_fraction": verification["total_fraction"],
        "is_consistent": verification["is_consistent"],
    }
    return normalized
