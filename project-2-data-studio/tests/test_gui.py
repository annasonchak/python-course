import tkinter as tk

import pandas as pd
import pytest

from studio.gui import App
from studio.session import DataSession


@pytest.fixture
def app():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Brak środowiska graficznego")
    root.withdraw()
    application = App(root)
    yield application
    root.destroy()


def load_frame(application: App) -> None:
    frame = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "score": [10.0, None, 30.0, 1000.0],
        "city": ["A", "B", "A", "B"],
    })
    application.session = DataSession(frame)
    application.refresh_all()


def test_controls_refresh_after_loading_data(app):
    load_frame(app)

    assert list(app.column_combo["values"]) == ["id", "score", "city"]
    assert len(app.profile_table.get_children()) == 3


def test_draw_plot_embeds_canvas_and_replaces_previous_one(app):
    load_frame(app)
    app.column_choice.set("score")
    app.plot_x_choice.set("score")

    app.plot_type_choice.set("histogram")
    app.on_draw_plot()
    first_canvas = app.plot_canvas

    app.plot_type_choice.set("box")
    app.on_draw_plot()

    assert first_canvas is not None
    assert app.plot_canvas is not first_canvas
    assert len(app.plot_area.winfo_children()) == 1


def test_reset_restores_data_in_gui(app):
    load_frame(app)
    app.column_choice.set("score")
    app.strategy_choice.set("median")
    app.on_handle_missing()
    assert app.session.current["score"].isna().sum() == 0

    app.on_reset()

    assert app.session.current["score"].isna().sum() == 1
    assert len(app.log_table.get_children()) >= 2

def test_preview_and_statistics_refresh(app):
    load_frame(app)

    assert len(app.preview_table.get_children()) == 4
    assert list(app.preview_table["columns"]) == ["id", "score", "city"]
    assert len(app.statistics_table.get_children()) == 2  # id i score