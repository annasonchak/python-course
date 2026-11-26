from pathlib import Path

import pandas as pd
import pytest
from matplotlib.figure import Figure

from studio.errors import ValidationError
from studio.plots import box_plot_figure, histogram_figure
from studio.session import DataSession

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def make_session() -> DataSession:
    frame = pd.DataFrame({
        "score": [1, 2, 2, 3, 4, 5, 100],
        "city": ["A", "B", "A", "C", "A", "B", "C"],
        "constant": [7, 7, 7, 7, 7, 7, 7],
        "empty": [float("nan")] * 7,
    })
    return DataSession(frame)


def test_histogram_returns_figure_with_title_and_axis_labels():
    figure = histogram_figure(make_session(), "score")
    axes = figure.axes[0]

    assert isinstance(figure, Figure)
    assert "score" in axes.get_title()
    assert axes.get_xlabel() == "score"
    assert axes.get_ylabel() != ""


def test_histogram_counts_all_values_without_missing():
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0, None]})
    figure = histogram_figure(DataSession(frame), "x")
    axes = figure.axes[0]

    total_height = 0
    for bar in axes.patches:
        total_height += bar.get_height()

    assert total_height == 3


def test_box_plot_returns_figure_with_title_and_axis_labels():
    figure = box_plot_figure(make_session(), "score")
    axes = figure.axes[0]

    assert isinstance(figure, Figure)
    assert "score" in axes.get_title()
    assert axes.get_xlabel() != ""
    assert axes.get_ylabel() == "score"


def test_constant_column_is_blocked_for_both_plots():
    session = make_session()

    with pytest.raises(ValidationError, match="stała"):
        histogram_figure(session, "constant")
    with pytest.raises(ValidationError, match="stała"):
        box_plot_figure(session, "constant")


def test_text_column_is_blocked_for_both_plots():
    session = make_session()

    with pytest.raises(ValidationError, match="nie jest liczbowa"):
        histogram_figure(session, "city")
    with pytest.raises(ValidationError, match="nie jest liczbowa"):
        box_plot_figure(session, "city")


def test_unknown_column_is_blocked():
    with pytest.raises(ValidationError, match="nie istnieje"):
        histogram_figure(make_session(), "nie_ma")


def test_column_with_only_missing_values_is_blocked():
    with pytest.raises(ValidationError, match="nie zawiera żadnych wartości"):
        histogram_figure(make_session(), "empty")


def test_plots_do_not_change_session_data():
    session = make_session()

    histogram_figure(session, "score")
    box_plot_figure(session, "score")

    assert session.current["score"].tolist() == [1, 2, 2, 3, 4, 5, 100]
    assert len(session.audit_log) == 0


def test_figure_can_be_saved_as_png_and_svg(tmp_path):
    figure = histogram_figure(make_session(), "score")

    png_path = tmp_path / "histogram.png"
    svg_path = tmp_path / "histogram.svg"
    figure.savefig(png_path)
    figure.savefig(svg_path)

    assert png_path.stat().st_size > 0
    assert svg_path.stat().st_size > 0


def test_plots_on_file_test_06_block_constant_and_text_columns():
    session = DataSession.from_csv(DATA_DIR / "test_06_stala_tekst.csv")

    with pytest.raises(ValidationError, match="stała"):
        histogram_figure(session, "constant")
    with pytest.raises(ValidationError, match="nie jest liczbowa"):
        box_plot_figure(session, "label")

    assert isinstance(histogram_figure(session, "id"), Figure)