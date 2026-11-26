from pathlib import Path

import pandas as pd
import pytest
from matplotlib.figure import Figure

from studio.errors import ValidationError
from studio.plots import (
    bar_figure,
    box_plot_figure,
    correlation_figure,
    get_correlation_matrix,
    histogram_figure,
    scatter_figure,
)
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

def make_session_for_pairs() -> DataSession:
    frame = pd.DataFrame({
        "age": [10, 20, 30, 40, 50],
        "rooms": [3.0, 4.0, None, 6.0, 8.0],
        "region": ["A", "B", "A", "C", "A"],
        "constant": [1, 1, 1, 1, 1],
    })
    return DataSession(frame)


def test_scatter_returns_figure_with_title_and_axis_labels():
    figure = scatter_figure(make_session_for_pairs(), "age", "rooms")
    axes = figure.axes[0]

    assert isinstance(figure, Figure)
    assert "age" in axes.get_title() and "rooms" in axes.get_title()
    assert axes.get_xlabel() == "age"
    assert axes.get_ylabel() == "rooms"


def test_scatter_skips_rows_with_missing_values():
    figure = scatter_figure(make_session_for_pairs(), "age", "rooms")
    axes = figure.axes[0]

    point_count = len(axes.collections[0].get_offsets())

    assert point_count == 4


def test_scatter_blocks_same_column_text_and_constant():
    session = make_session_for_pairs()

    with pytest.raises(ValidationError, match="tę samą kolumnę"):
        scatter_figure(session, "age", "age")
    with pytest.raises(ValidationError, match="nie jest liczbowa"):
        scatter_figure(session, "age", "region")
    with pytest.raises(ValidationError, match="stała"):
        scatter_figure(session, "age", "constant")


def test_bar_returns_figure_with_correct_counts():
    figure = bar_figure(make_session_for_pairs(), "region")
    axes = figure.axes[0]

    heights = []
    for bar in axes.patches:
        heights.append(bar.get_height())

    assert isinstance(figure, Figure)
    assert heights == [3, 1, 1]
    assert axes.get_xlabel() == "region"
    assert axes.get_ylabel() != ""


def test_bar_blocks_numeric_column():
    with pytest.raises(ValidationError, match="jest liczbowa"):
        bar_figure(make_session_for_pairs(), "age")


def test_bar_blocks_too_many_categories():
    names = []
    for number in range(30):
        names.append(f"kategoria_{number}")
    session = DataSession(pd.DataFrame({"name": names}))

    with pytest.raises(ValidationError, match="limit"):
        bar_figure(session, "name")


def test_bar_blocks_unknown_column():
    with pytest.raises(ValidationError, match="nie istnieje"):
        bar_figure(make_session_for_pairs(), "nie_ma")


def test_scatter_and_bar_do_not_change_session_data():
    session = make_session_for_pairs()

    scatter_figure(session, "age", "rooms")
    bar_figure(session, "region")

    assert session.current["age"].tolist() == [10, 20, 30, 40, 50]
    assert len(session.audit_log) == 0

def make_session_for_correlation() -> DataSession:
    frame = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "double_x": [2, 4, 6, 8, 10],
        "reverse_x": [5, 4, 3, 2, 1],
        "constant": [3, 3, 3, 3, 3],
        "label": ["a", "b", "c", "d", "e"],
    })
    return DataSession(frame)


def test_correlation_matrix_has_expected_values():
    matrix = get_correlation_matrix(make_session_for_correlation())

    assert matrix.loc["x", "double_x"] == pytest.approx(1.0)
    assert matrix.loc["x", "reverse_x"] == pytest.approx(-1.0)


def test_correlation_matrix_skips_constant_and_text_columns():
    matrix = get_correlation_matrix(make_session_for_correlation())

    assert list(matrix.columns) == ["x", "double_x", "reverse_x"]


def test_correlation_figure_has_title_labels_and_causation_warning():
    figure = correlation_figure(make_session_for_correlation())
    axes = figure.axes[0]

    texts = []
    for text in figure.texts:
        texts.append(text.get_text())

    assert isinstance(figure, Figure)
    assert "korelacji" in axes.get_title()
    assert axes.get_xlabel() != ""
    assert any("przyczynowości" in text for text in texts)


def test_correlation_blocked_with_fewer_than_two_numeric_columns():
    session = DataSession(pd.DataFrame({"x": [1, 2, 3], "label": ["a", "b", "c"]}))

    with pytest.raises(ValidationError, match="co najmniej dwie"):
        correlation_figure(session)


def test_correlation_does_not_change_session_data():
    session = make_session_for_correlation()

    correlation_figure(session)

    assert session.current["x"].tolist() == [1, 2, 3, 4, 5]
    assert len(session.audit_log) == 0