"""Skrypt Lab. 6: raport przed/po i zapis cleaned.csv.

Użycie:  python run_pipeline.py data/test_04_zakres_outlier.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from studio.cleaning import (
    drop_exact_duplicates,
    fill_missing_with_statistic,
    handle_outliers,
    report_out_of_range,
)
from studio.errors import StudioError
from studio.profiling import build_profile
from studio.reporting import save_audit_report, save_cleaned_csv
from studio.session import DataSession

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
RANGE_RULES = {"HouseAge": (0, 100),} # bo do wynikowego csv wpadało -5 :\

def print_profile(title: str, session: DataSession, use_raw: bool) -> None:
    if use_raw:
        frame = session.raw
    else:
        frame = session.current

    profile = build_profile(frame)
    print(f"--- {title} ---")
    print(f"Rekordy: {profile.row_count}, kolumny: {profile.column_count}")
    print(f"Pełne duplikaty: {profile.duplicate_count}")
    print(profile.columns.to_string(index=False))
    print()


def run(path: Path, output_dir: Path = OUTPUT_DIR) -> None:
    session = DataSession.from_csv(path)
    print_profile("PRZED", session, use_raw=True)

    drop_exact_duplicates(session)

    for column_name in list(session.current.columns):
        column = session.current[column_name]
        if column.isna().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(column):
            fill_missing_with_statistic(session, [column_name], "median")
        else:
            fill_missing_with_statistic(session, [column_name], "mode")

    for column_name in session.current.select_dtypes(include="number").columns:
        if column_name == "id":
            continue
        # 'keep' tylko raportuje regułę, niczego nie usuwa automatycznie
        handle_outliers(session, column_name, "keep")

    for column_name, limits in RANGE_RULES.items():
        if column_name not in session.current.columns:
            continue
        minimum, maximum = limits
        found_count = report_out_of_range(session, column_name, minimum, maximum)
        print(f"Reguła zakresu {column_name} [{minimum}, {maximum}]: znaleziono {found_count}")

    print_profile("PO", session, use_raw=False)

    output_dir.mkdir(exist_ok=True)
    save_cleaned_csv(session, output_dir / "cleaned.csv")
    save_audit_report(session, output_dir / "audit_report.txt")
    save_audit_report(session, output_dir / "audit_report.csv")
    print(f"Zapisano pliki w: {output_dir}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Podaj ścieżkę do pliku CSV, np. data/test_04_zakres_outlier.csv")
        return

    try:
        run(Path(sys.argv[1]))
    except StudioError as error:
        print(f"Błąd: {error}")


if __name__ == "__main__":
    main()