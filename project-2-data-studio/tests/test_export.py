from pathlib import Path

import pandas as pd

from studio.cleaning import drop_exact_duplicates, fill_missing_with_statistic
from studio.plots import histogram_figure
from studio.reporting import save_audit_report, save_cleaned_csv, save_figure
from studio.session import DataSession

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_full_export_cycle_can_be_read_again(tmp_path):
    session = DataSession.from_csv(DATA_DIR / "test_03_braki_duplikaty.csv")
    drop_exact_duplicates(session)
    fill_missing_with_statistic(session, ["value"], "median")

    cleaned_path = save_cleaned_csv(session, tmp_path / "cleaned.csv")
    reloaded = DataSession.from_csv(cleaned_path)

    assert reloaded.raw.shape == session.current.shape
    assert reloaded.raw["value"].tolist() == session.current["value"].tolist()
    assert reloaded.raw["id"].tolist() == [1, 2, 3, 4]


def test_exported_plots_and_report_exist_and_are_not_empty(tmp_path):
    session = DataSession.from_csv(DATA_DIR / "test_04_zakres_outlier.csv")
    figure = histogram_figure(session, "AveRooms")

    paths = [
        save_figure(figure, tmp_path / "wykres.png"),
        save_figure(figure, tmp_path / "wykres.pdf"),
        save_figure(figure, tmp_path / "wykres.svg"),
        save_audit_report(session, tmp_path / "raport.txt"),
    ]

    for path in paths:
        assert path.stat().st_size > 0