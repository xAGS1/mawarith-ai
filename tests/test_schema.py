from backend.schemas.case import InheritanceOutput


def test_minimal_schema():
    obj = InheritanceOutput(
        heirs=[],
        blocked=[],
        shares=[],
        awl_or_radd="none",
        post_tasil={"total_shares": None, "distribution": []},
    )
    assert obj.awl_or_radd == "none"
