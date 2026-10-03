from fractions import Fraction
from functools import reduce
from math import gcd


def lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


def lcm_many(numbers):
    return reduce(lcm, numbers, 1)


def verify_distribution(distribution):
    individual_fractions = []

    for item in distribution:
        count = item["count"]
        fraction_text = item["per_head_shares"]

        fraction = Fraction(fraction_text)

        for _ in range(count):
            individual_fractions.append(fraction)

    if not individual_fractions:
        return {
            "total_shares": 0,
            "total_fraction": "0",
            "is_consistent": False,
            "distribution": [],
        }

    denominators = [
        fraction.denominator
        for fraction in individual_fractions
    ]

    total_shares = lcm_many(denominators)

    total_fraction = sum(
        individual_fractions,
        Fraction(0, 1),
    )

    normalized_distribution = []

    for item in distribution:
        fraction = Fraction(
            item["per_head_shares"]
        )

        numerator_on_common_base = (
            fraction.numerator
            * (
                total_shares
                // fraction.denominator
            )
        )

        normalized_distribution.append(
            {
                "heir": item["heir"],
                "count": item["count"],
                "per_head_shares": (
                    f"{numerator_on_common_base}"
                    f"/{total_shares}"
                ),
                "per_head_percent": round(
                    float(fraction) * 100,
                    2,
                ),
            }
        )

    return {
        "total_shares": total_shares,
        "total_fraction": str(total_fraction),
        "is_consistent": (
            total_fraction == Fraction(1, 1)
        ),
        "distribution": normalized_distribution,
    }
