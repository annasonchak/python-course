"""Generuje pliki do oddania w katalogu output/ (cleaned.csv, raport, wykresy)."""
from __future__ import annotations

from pathlib import Path

from studio.cleaning import (
    apply_range_rule,
    drop_exact_duplicates,
    fill_missing_with_statistic,
    handle_outliers,
)
from studio.plots import box_plot_figure, correlation_figure, histogram_figure, scatter_figure
from studio.reporting import save_audit_report, save_cleaned_csv, save_figure
from studio.session import DataSession

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SOURCE = Path(__file__).resolve().parent / "data" / "test_04_zakres_outlier.csv"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    session = DataSession.from_csv(SOURCE)

    save_figure(box_plot_figure(session, "AveRooms"), OUTPUT_DIR / "box_przed.png")
    save_figure(histogram_figure(session, "AveRooms"), OUTPUT_DIR / "histogram_przed.png")

    drop_exact_duplicates(session)
    fill_missing_with_statistic(session, ["HouseAge"], "median")
    apply_range_rule(session, "HouseAge", 0, 100, "to_missing")
    fill_missing_with_statistic(session, ["HouseAge"], "median")
    handle_outliers(session, "AveRooms", "clip")

    save_figure(box_plot_figure(session, "AveRooms"), OUTPUT_DIR / "box_po.png")
    save_figure(scatter_figure(session, "HouseAge", "AveRooms"), OUTPUT_DIR / "scatter_po.pdf")
    save_figure(correlation_figure(session), OUTPUT_DIR / "korelacja_po.svg")

    save_cleaned_csv(session, OUTPUT_DIR / "cleaned.csv")
    save_audit_report(session, OUTPUT_DIR / "audit_report.txt")
    print(f"Zapisano pliki w {OUTPUT_DIR}")


if __name__ == "__main__":
    main()