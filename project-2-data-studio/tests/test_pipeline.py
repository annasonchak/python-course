from pathlib import Path

import pandas as pd

from run_pipeline import run

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_pipeline_on_missing_and_duplicates_file(tmp_path):
    # test_03: dwa identyczne wiersze, brak w value (mediana) i w group (dominanta)
    run(DATA_DIR / "test_03_braki_duplikaty.csv", tmp_path)

    cleaned = pd.read_csv(tmp_path / "cleaned.csv")

    assert len(cleaned) == 4
    assert cleaned["id"].tolist() == [1, 2, 3, 4]
    assert cleaned["value"].tolist() == [10.0, 30.0, 30.0, 40.0]
    assert cleaned["group"].tolist() == ["A", "B", "A", "C"]


def test_pipeline_does_not_remove_outliers_automatically(tmp_path):
    # test_04: wartości -5 i 1000 mają zostać, a reguła trafia do raportu
    run(DATA_DIR / "test_04_zakres_outlier.csv", tmp_path)

    cleaned = pd.read_csv(tmp_path / "cleaned.csv")
    report = (tmp_path / "audit_report.txt").read_text(encoding="utf-8")

    assert len(cleaned) == 8
    assert cleaned["HouseAge"].min() == -5
    assert cleaned["AveRooms"].max() == 1000
    assert "handle_outliers" in report
    assert "IQR" in report


def test_pipeline_results_are_repeatable(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    run(DATA_DIR / "test_03_braki_duplikaty.csv", first_dir)
    run(DATA_DIR / "test_03_braki_duplikaty.csv", second_dir)

    first_text = (first_dir / "cleaned.csv").read_text(encoding="utf-8")
    second_text = (second_dir / "cleaned.csv").read_text(encoding="utf-8")
    assert first_text == second_text

from studio.cleaning import find_out_of_range, find_outliers_iqr
from studio.session import DataSession


def test_range_rule_catches_negative_age_that_iqr_misses():
    session = DataSession.from_csv(DATA_DIR / "test_04_zakres_outlier.csv")

    iqr_mask = find_outliers_iqr(session, "HouseAge")
    range_mask = find_out_of_range(session, "HouseAge", 0, 100)

    assert iqr_mask.sum() == 0
    assert range_mask.sum() == 1
    assert session.current.loc[range_mask, "id"].tolist() == [2]

def test_pipeline_report_shows_negative_age_from_range_rule(tmp_path):
    run(DATA_DIR / "test_04_zakres_outlier.csv", tmp_path)

    report = (tmp_path / "audit_report.txt").read_text(encoding="utf-8")

    assert "check_range_rule" in report
    assert "'found': 1" in report