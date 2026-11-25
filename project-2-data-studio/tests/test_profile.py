import pandas as pd

from studio.profiling import build_column_profile, get_shape


def make_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "age": [20, 21, None, 21],
        "city": ["Opole", "Opole", "Łódź", None],
    })


def test_get_shape_returns_rows_and_columns():
    assert get_shape(make_frame()) == (4, 2)


def test_profile_has_one_row_per_column():
    profile = build_column_profile(make_frame())
    assert list(profile["column"]) == ["age", "city"]


def test_profile_counts_missing_values_and_percent():
    profile = build_column_profile(make_frame())
    age_row = profile[profile["column"] == "age"].iloc[0]
    assert age_row["missing"] == 1
    assert age_row["missing_pct"] == 25.0


def test_profile_counts_unique_values_without_missing():
    profile = build_column_profile(make_frame())
    age_row = profile[profile["column"] == "age"].iloc[0]
    city_row = profile[profile["column"] == "city"].iloc[0]
    assert age_row["unique"] == 2
    assert city_row["unique"] == 2


def test_profile_reports_dtype_as_text():
    profile = build_column_profile(make_frame())
    age_row = profile[profile["column"] == "age"].iloc[0]
    assert age_row["dtype"] == "float64"