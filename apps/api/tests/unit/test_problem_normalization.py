from codemuscle.application.problems.normalization import (
    normalize_name,
    normalize_title,
    normalize_url,
)


def test_normalize_problem_values() -> None:
    assert normalize_name("  Dynamic   Programming ") == "dynamic programming"
    assert normalize_title("Two Sum! (Classic)") == "two sum classic"
    assert normalize_url("HTTPS://LeetCode.com/problems/two-sum/#notes") == (
        "https://leetcode.com/problems/two-sum"
    )
