import pandas as pd
import pytest

from studio.cleaning import (
    apply_range_rule,
    drop_exact_duplicates,
    drop_rows_with_missing,
    fill_missing_with_constant,
    fill_missing_with_statistic,
    find_out_of_range,
    find_outliers_iqr,
    handle_outliers,
    report_out_of_range,
)
from studio.errors import ValidationError
from studio.session import DataSession

def make_frame_with_duplicate() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 2, 3],
        "group": ["A", "B", "B", "B"],
    })


def test_drop_exact_duplicates_removes_only_full_copies():
    session = DataSession(make_frame_with_duplicate())

    removed_count = drop_exact_duplicates(session)

    assert removed_count == 1
    assert len(session.current) == 3
    assert session.current["id"].tolist() == [1, 2, 3]


def test_drop_exact_duplicates_does_not_change_raw():
    session = DataSession(make_frame_with_duplicate())

    drop_exact_duplicates(session)

    assert len(session.raw) == 4


def test_drop_exact_duplicates_writes_audit_entry():
    session = DataSession(make_frame_with_duplicate())

    drop_exact_duplicates(session)

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "drop_exact_duplicates"
    assert last_entry.rows_before == 4
    assert last_entry.rows_after == 3
    assert last_entry.affected == 1


def test_drop_exact_duplicates_when_none_found_changes_nothing():
    session = DataSession(pd.DataFrame({"id": [1, 2, 3]}))

    removed_count = drop_exact_duplicates(session)

    assert removed_count == 0
    assert len(session.current) == 3
    assert session.audit_log[-1].affected == 0

def make_frame_with_missing() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3],
        "value": [10.0, None, 30.0],
        "group": ["A", "B", None],
    })


def test_drop_rows_with_missing_removes_rows_missing_in_selected_column():
    session = DataSession(make_frame_with_missing())

    removed_count = drop_rows_with_missing(session, ["value"])

    assert removed_count == 1
    assert session.current["id"].tolist() == [1, 3]


def test_drop_rows_with_missing_ignores_other_columns():
    session = DataSession(make_frame_with_missing())

    removed_count = drop_rows_with_missing(session, ["group"])

    assert removed_count == 1
    assert session.current["id"].tolist() == [1, 2]


def test_drop_rows_with_missing_does_not_change_raw():
    session = DataSession(make_frame_with_missing())

    drop_rows_with_missing(session, ["value"])

    assert len(session.raw) == 3


def test_drop_rows_with_missing_writes_audit_entry():
    session = DataSession(make_frame_with_missing())

    drop_rows_with_missing(session, ["value"])

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "drop_rows_with_missing"
    assert last_entry.rows_before == 3
    assert last_entry.rows_after == 2
    assert last_entry.affected == 1


def test_fill_missing_with_constant_in_numeric_column():
    session = DataSession(make_frame_with_missing())

    filled_count = fill_missing_with_constant(session, ["value"], "0")

    assert filled_count == 1
    assert session.current["value"].tolist() == [10.0, 0.0, 30.0]
    assert len(session.current) == 3


def test_fill_missing_with_constant_in_text_column():
    session = DataSession(make_frame_with_missing())

    fill_missing_with_constant(session, ["group"], "brak")

    assert session.current["group"].tolist() == ["A", "B", "brak"]
    assert session.raw["group"].isna().sum() == 1


def test_fill_missing_with_constant_writes_audit_entry():
    session = DataSession(make_frame_with_missing())

    fill_missing_with_constant(session, ["value", "group"], "0")

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "fill_missing_with_constant"
    assert last_entry.rows_before == 3
    assert last_entry.rows_after == 3
    assert last_entry.affected == 2


def test_fill_numeric_column_with_text_raises_and_changes_nothing():
    session = DataSession(make_frame_with_missing())

    with pytest.raises(ValidationError, match="nie jest liczbą"):
        fill_missing_with_constant(session, ["value"], "abc")

    assert session.current["value"].isna().sum() == 1
    assert len(session.audit_log) == 0


def test_cleaning_without_selected_columns_raises_validation_error():
    session = DataSession(make_frame_with_missing())

    with pytest.raises(ValidationError, match="Nie wybrano"):
        drop_rows_with_missing(session, [])


def test_cleaning_with_unknown_column_raises_validation_error():
    session = DataSession(make_frame_with_missing())

    with pytest.raises(ValidationError, match="nie istnieje"):
        fill_missing_with_constant(session, ["nie_ma_takiej"], "0")

def make_frame_for_statistics() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "score": [10.0, 20.0, None, 30.0, 1000.0],
        "city": ["Opole", "Opole", None, "Łódź", "Opole"],
    })


def test_fill_missing_with_mean():
    session = DataSession(make_frame_for_statistics())

    # ma tu wybrać 265.0
    filled_count = fill_missing_with_statistic(session, ["score"], "mean")

    assert filled_count == 1
    assert session.current["score"].tolist() == [10.0, 20.0, 265.0, 30.0, 1000.0]


def test_fill_missing_with_median_is_resistant_to_outlier():
    session = DataSession(make_frame_for_statistics())

    fill_missing_with_statistic(session, ["score"], "median")

    assert session.current.loc[2, "score"] == 25.0


def test_fill_missing_with_mode_in_text_column():
    session = DataSession(make_frame_for_statistics())

    fill_missing_with_statistic(session, ["city"], "mode")

    assert session.current.loc[2, "city"] == "Opole"


def test_fill_missing_with_statistic_does_not_touch_other_columns():
    session = DataSession(make_frame_for_statistics())

    fill_missing_with_statistic(session, ["score"], "mean")

    assert session.current["city"].isna().sum() == 1
    assert session.raw["score"].isna().sum() == 1


def test_fill_missing_with_statistic_writes_audit_entry():
    session = DataSession(make_frame_for_statistics())

    fill_missing_with_statistic(session, ["score", "city"], "mode")

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "fill_missing_with_statistic"
    assert last_entry.params["strategy"] == "mode"
    assert last_entry.rows_before == 5
    assert last_entry.rows_after == 5
    assert last_entry.affected == 2


def test_mean_on_text_column_raises_and_changes_nothing():
    session = DataSession(make_frame_for_statistics())

    with pytest.raises(ValidationError, match="wymaga kolumny liczbowej"):
        fill_missing_with_statistic(session, ["city"], "mean")

    assert session.current["city"].isna().sum() == 1
    assert len(session.audit_log) == 0


def test_unknown_strategy_raises_validation_error():
    session = DataSession(make_frame_for_statistics())

    with pytest.raises(ValidationError, match="Nieznana strategia"):
        fill_missing_with_statistic(session, ["score"], "average")

def make_frame_for_range() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "age": [10, -5, 20, 1000],
        "city": ["A", "B", "C", "D"],
    })


def test_find_out_of_range_detects_both_sides():
    session = DataSession(make_frame_for_range())

    mask = find_out_of_range(session, "age", 0, 100)

    assert mask.tolist() == [False, True, False, True]


def test_find_out_of_range_with_only_minimum():
    session = DataSession(make_frame_for_range())

    mask = find_out_of_range(session, "age", 0, None)

    assert mask.tolist() == [False, True, False, False]


def test_find_out_of_range_does_not_change_data():
    session = DataSession(make_frame_for_range())

    find_out_of_range(session, "age", 0, 100)

    assert session.current["age"].tolist() == [10, -5, 20, 1000]
    assert len(session.audit_log) == 0


def test_find_out_of_range_ignores_missing_values():
    frame = pd.DataFrame({"age": [10.0, None, 200.0]})
    session = DataSession(frame)

    mask = find_out_of_range(session, "age", 0, 100)

    assert mask.tolist() == [False, False, True]


def test_report_out_of_range_counts_and_logs_without_changes():
    session = DataSession(make_frame_for_range())

    found_count = report_out_of_range(session, "age", 0, 100)

    assert found_count == 2
    assert session.current["age"].tolist() == [10, -5, 20, 1000]
    last_entry = session.audit_log[-1]
    assert last_entry.operation == "check_range_rule"
    assert last_entry.affected == 0
    assert last_entry.rows_before == 4
    assert last_entry.rows_after == 4


def test_range_with_minimum_greater_than_maximum_raises():
    session = DataSession(make_frame_for_range())

    with pytest.raises(ValidationError, match="większe niż maksimum"):
        find_out_of_range(session, "age", 100, 0)


def test_range_without_any_limit_raises():
    session = DataSession(make_frame_for_range())

    with pytest.raises(ValidationError, match="Nie podano"):
        find_out_of_range(session, "age", None, None)


def test_range_on_text_column_raises():
    session = DataSession(make_frame_for_range())

    with pytest.raises(ValidationError, match="nie jest liczbowa"):
        find_out_of_range(session, "city", 0, 100)

def test_apply_range_rule_to_missing_replaces_only_bad_values():
    session = DataSession(make_frame_for_range())

    affected_count = apply_range_rule(session, "age", 0, 100, "to_missing")

    assert affected_count == 2
    assert len(session.current) == 4
    assert session.current["age"].isna().tolist() == [False, True, False, True]
    assert session.current.loc[0, "age"] == 10
    assert session.current.loc[2, "age"] == 20


def test_apply_range_rule_drop_rows_removes_bad_rows():
    session = DataSession(make_frame_for_range())

    affected_count = apply_range_rule(session, "age", 0, 100, "drop_rows")

    assert affected_count == 2
    assert session.current["id"].tolist() == [1, 3]


def test_apply_range_rule_does_not_touch_other_columns_or_raw():
    session = DataSession(make_frame_for_range())

    apply_range_rule(session, "age", 0, 100, "to_missing")

    assert session.current["city"].tolist() == ["A", "B", "C", "D"]
    assert session.raw["age"].tolist() == [10, -5, 20, 1000]


def test_apply_range_rule_writes_audit_entry():
    session = DataSession(make_frame_for_range())

    apply_range_rule(session, "age", 0, 100, "drop_rows")

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "apply_range_rule"
    assert last_entry.params["action"] == "drop_rows"
    assert last_entry.rows_before == 4
    assert last_entry.rows_after == 2
    assert last_entry.affected == 2


def test_apply_range_rule_with_unknown_action_raises_and_changes_nothing():
    session = DataSession(make_frame_for_range())

    with pytest.raises(ValidationError, match="Nieznana akcja"):
        apply_range_rule(session, "age", 0, 100, "delete_everything")

    assert session.current["age"].tolist() == [10, -5, 20, 1000]
    assert len(session.audit_log) == 0


def test_apply_range_rule_with_invalid_range_raises_and_changes_nothing():
    session = DataSession(make_frame_for_range())

    with pytest.raises(ValidationError, match="większe niż maksimum"):
        apply_range_rule(session, "age", 100, 0, "drop_rows")

    assert len(session.current) == 4
    assert len(session.audit_log) == 0

def make_frame_for_outliers() -> pd.DataFrame:
    # Q1 = 11.75, Q3 = 15.25, IQR = 3.5, granice: 6.5 i 20.5. Odstająca jest tylko 1000.
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6, 7, 8],
        "value": [10, 11, 12, 13, 14, 15, 16, 1000],
        "label": ["a", "b", "c", "d", "e", "f", "g", "h"],
    })


def test_find_outliers_iqr_detects_only_extreme_value():
    session = DataSession(make_frame_for_outliers())

    mask = find_outliers_iqr(session, "value")

    assert mask.tolist() == [False, False, False, False, False, False, False, True]


def test_find_outliers_iqr_does_not_change_data_or_log():
    session = DataSession(make_frame_for_outliers())

    find_outliers_iqr(session, "value")

    assert session.current["value"].tolist() == [10, 11, 12, 13, 14, 15, 16, 1000]
    assert len(session.audit_log) == 0


def test_find_outliers_iqr_on_constant_column_finds_nothing():
    session = DataSession(pd.DataFrame({"value": [5, 5, 5, 5]}))

    mask = find_outliers_iqr(session, "value")

    assert mask.sum() == 0


def test_handle_outliers_flag_adds_column_and_keeps_values():
    session = DataSession(make_frame_for_outliers())

    found_count = handle_outliers(session, "value", "flag")

    assert found_count == 1
    assert session.current["value"].tolist() == [10, 11, 12, 13, 14, 15, 16, 1000]
    assert bool(session.current["value_outlier"].iloc[-1]) is True
    assert session.current["value_outlier"].sum() == 1


def test_handle_outliers_clip_limits_value_to_upper_bound():
    session = DataSession(make_frame_for_outliers())

    handle_outliers(session, "value", "clip")

    assert len(session.current) == 8
    assert session.current["value"].iloc[-1] == 20.5
    assert session.current["value"].iloc[0] == 10


def test_handle_outliers_drop_removes_rows():
    session = DataSession(make_frame_for_outliers())

    handle_outliers(session, "value", "drop")

    assert session.current["id"].tolist() == [1, 2, 3, 4, 5, 6, 7]
    assert len(session.raw) == 8


def test_handle_outliers_keep_changes_nothing_but_logs_rule():
    session = DataSession(make_frame_for_outliers())

    found_count = handle_outliers(session, "value", "keep")

    assert found_count == 1
    assert session.current["value"].tolist() == [10, 11, 12, 13, 14, 15, 16, 1000]
    last_entry = session.audit_log[-1]
    assert last_entry.operation == "handle_outliers"
    assert last_entry.affected == 0
    assert last_entry.params["found"] == 1
    assert last_entry.params["method"] == "IQR"


def test_handle_outliers_drop_writes_audit_entry():
    session = DataSession(make_frame_for_outliers())

    handle_outliers(session, "value", "drop")

    last_entry = session.audit_log[-1]
    assert last_entry.rows_before == 8
    assert last_entry.rows_after == 7
    assert last_entry.affected == 1
    assert last_entry.params["bounds"] == (6.5, 20.5)


def test_handle_outliers_unknown_action_raises_and_changes_nothing():
    session = DataSession(make_frame_for_outliers())

    with pytest.raises(ValidationError, match="Nieznana akcja"):
        handle_outliers(session, "value", "remove_all")

    assert len(session.current) == 8
    assert len(session.audit_log) == 0


def test_handle_outliers_on_text_column_raises():
    session = DataSession(make_frame_for_outliers())

    with pytest.raises(ValidationError, match="nie jest liczbowa"):
        handle_outliers(session, "label", "flag")


def test_handle_outliers_with_non_positive_factor_raises():
    session = DataSession(make_frame_for_outliers())

    with pytest.raises(ValidationError, match="dodatni"):
        handle_outliers(session, "value", "flag", factor=0)