import pandas as pd
from pathlib import Path

from studio.profiling import build_column_profile, get_shape

from studio.profiling import (
    build_column_profile,
    build_numeric_statistics,
    build_profile,
    count_exact_duplicates,
    get_shape,
)
from studio.session import DataSession

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

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
    
def test_count_exact_duplicates_counts_only_full_copies():
    frame = pd.DataFrame({
        "id": [1, 2, 2, 3],
        "group": ["A", "B", "B", "B"],
    })
    assert count_exact_duplicates(frame) == 1


def test_count_exact_duplicates_is_zero_for_unique_rows():
    frame = pd.DataFrame({"id": [1, 2, 3]})
    assert count_exact_duplicates(frame) == 0


def test_numeric_statistics_contains_only_numeric_columns():
    frame = pd.DataFrame({
        "age": [10, 20, 30],
        "city": ["A", "B", "C"],
    })
    statistics = build_numeric_statistics(frame)
    assert list(statistics["column"]) == ["age"]


def test_numeric_statistics_values_are_correct():
    frame = pd.DataFrame({"age": [10, 20, 30]})
    statistics = build_numeric_statistics(frame)
    age_row = statistics.iloc[0]
    assert age_row["min"] == 10
    assert age_row["max"] == 30
    assert age_row["mean"] == 20
    assert age_row["50%"] == 20


def test_numeric_statistics_is_empty_when_no_numeric_columns():
    frame = pd.DataFrame({"city": ["A", "B"]})
    assert build_numeric_statistics(frame).empty

def test_build_profile_on_missing_and_duplicates_file():
    session = DataSession.from_csv(DATA_DIR / "test_03_braki_duplikaty.csv")
    profile = build_profile(session.raw)

    assert profile.row_count == 5
    assert profile.column_count == 3
    assert profile.duplicate_count == 1

    value_row = profile.columns[profile.columns["column"] == "value"].iloc[0]
    group_row = profile.columns[profile.columns["column"] == "group"].iloc[0]
    assert value_row["missing"] == 2
    assert group_row["missing"] == 1


def test_build_profile_shows_extreme_values_in_statistics():
    session = DataSession.from_csv(DATA_DIR / "test_04_zakres_outlier.csv")
    profile = build_profile(session.raw)

    statistics = profile.statistics.set_index("column")
    assert statistics.loc["HouseAge", "min"] == -5
    assert statistics.loc["AveRooms", "max"] == 1000