"""Interfejs graficzny. Nie zawiera logiki biznesowej, tylko wywołuje moduły studio."""
from __future__ import annotations

import pandas as pd
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from studio.reporting import save_audit_report, save_cleaned_csv, save_figure

from studio.cleaning import (
    apply_range_rule,
    drop_exact_duplicates,
    drop_rows_with_missing,
    fill_missing_with_constant,
    fill_missing_with_statistic,
    find_outliers_iqr,
    handle_outliers,
    report_out_of_range,
)

from studio.plots import (
    bar_figure,
    box_plot_figure,
    correlation_figure,
    histogram_figure,
    scatter_figure,
)

from studio.errors import StudioError
from studio.profiling import build_numeric_statistics, build_profile
from studio.session import DataSession
from studio.errors import StudioError, ValidationError

PREVIEW_ROW_LIMIT = 100
STATISTIC_NAMES = ("count", "mean", "std", "min", "25%", "50%", "75%", "max")

class App:
    """Główne okno aplikacji. Cały stan sesji jest polem tego obiektu."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.session: DataSession | None = None

        self.root.title("Studio jakości i wizualizacji danych")
        self.root.geometry("1100x950")

        self.status_text = tk.StringVar(value="Wybierz plik CSV, aby rozpocząć.")
        self.file_text = tk.StringVar(value="Brak wczytanego pliku")

        self.summary_text = tk.StringVar(value="")
        self.column_choice = tk.StringVar(value="")
        self.strategy_choice = tk.StringVar(value="median")
        self.constant_text = tk.StringVar(value="0")

        self.minimum_text = tk.StringVar(value="")
        self.maximum_text = tk.StringVar(value="")
        self.range_action_choice = tk.StringVar(value="to_missing")
        self.iqr_factor_text = tk.StringVar(value="1.5")
        self.outlier_action_choice = tk.StringVar(value="flag")

        self.plot_type_choice = tk.StringVar(value="histogram")
        self.plot_x_choice = tk.StringVar(value="")
        self.plot_y_choice = tk.StringVar(value="")
        self.current_figure: Figure | None = None
        self.plot_canvas: FigureCanvasTkAgg | None = None

        self.build_widgets()

    def build_widgets(self) -> None:
        # --- Górny pasek i pasek statusu (poza zakładkami) ---
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side="top", fill="x")

        open_button = ttk.Button(top_frame, text="Wybierz plik CSV", command=self.on_open_file)
        open_button.pack(side="left")

        file_label = ttk.Label(top_frame, textvariable=self.file_text)
        file_label.pack(side="left", padx=10)

        ttk.Button(top_frame, text="Zapisz CSV", command=self.on_save_csv).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Zapisz raport", command=self.on_save_report).pack(side="left", padx=5)

        status_bar = ttk.Label(self.root, textvariable=self.status_text, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

        # --- Zakładki ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        data_tab = ttk.Frame(notebook, padding=5)
        preview_tab = ttk.Frame(notebook, padding=5)
        plots_tab = ttk.Frame(notebook, padding=5)
        log_tab = ttk.Frame(notebook, padding=5)
        notebook.add(data_tab, text="Dane i czyszczenie")
        notebook.add(preview_tab, text="Podgląd danych")
        notebook.add(plots_tab, text="Wykresy")
        notebook.add(log_tab, text="Dziennik zmian")

        self.build_data_tab(data_tab)
        self.build_preview_tab(preview_tab)
        self.build_plots_tab(plots_tab)
        self.build_log_tab(log_tab)

    def build_data_tab(self, parent: ttk.Frame) -> None:
        cleaning_frame = ttk.LabelFrame(parent, text="Czyszczenie", padding=10)
        cleaning_frame.pack(side="top", fill="x", pady=5)

        ttk.Button(
            cleaning_frame, text="Usuń duplikaty", command=self.on_drop_duplicates
        ).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(
            cleaning_frame, text="Resetuj dane", command=self.on_reset
        ).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(cleaning_frame, text="Kolumna:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.column_combo = ttk.Combobox(
            cleaning_frame, textvariable=self.column_choice, state="readonly", width=20
        )
        self.column_combo.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(cleaning_frame, text="Strategia braków:").grid(row=1, column=2, sticky="e", padx=5, pady=2)
        ttk.Combobox(
            cleaning_frame,
            textvariable=self.strategy_choice,
            values=["drop", "constant", "mean", "median", "mode"],
            state="readonly",
            width=12,
        ).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(cleaning_frame, text="Stała:").grid(row=1, column=4, sticky="e", padx=5, pady=2)
        ttk.Entry(cleaning_frame, textvariable=self.constant_text, width=10).grid(
            row=1, column=5, padx=5, pady=2
        )
        ttk.Button(
            cleaning_frame, text="Uzupełnij braki", command=self.on_handle_missing
        ).grid(row=1, column=6, padx=5, pady=2)

        range_frame = ttk.LabelFrame(
            parent, text="Reguła zakresu (dla kolumny wybranej wyżej)", padding=10
        )
        range_frame.pack(side="top", fill="x", pady=5)

        ttk.Label(range_frame, text="Minimum:").grid(row=0, column=0, padx=5, pady=2)
        ttk.Entry(range_frame, textvariable=self.minimum_text, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(range_frame, text="Maksimum:").grid(row=0, column=2, padx=5, pady=2)
        ttk.Entry(range_frame, textvariable=self.maximum_text, width=10).grid(row=0, column=3, padx=5)
        ttk.Label(range_frame, text="Akcja:").grid(row=0, column=4, padx=5, pady=2)
        ttk.Combobox(
            range_frame,
            textvariable=self.range_action_choice,
            values=["to_missing", "drop_rows"],
            state="readonly",
            width=12,
        ).grid(row=0, column=5, padx=5)
        ttk.Button(range_frame, text="Sprawdź", command=self.on_check_range).grid(row=0, column=6, padx=5)
        ttk.Button(range_frame, text="Zastosuj", command=self.on_apply_range).grid(row=0, column=7, padx=5)

        outlier_frame = ttk.LabelFrame(
            parent, text="Wartości odstające IQR (dla kolumny wybranej wyżej)", padding=10
        )
        outlier_frame.pack(side="top", fill="x", pady=5)

        ttk.Label(outlier_frame, text="Współczynnik:").grid(row=0, column=0, padx=5, pady=2)
        ttk.Entry(outlier_frame, textvariable=self.iqr_factor_text, width=8).grid(row=0, column=1, padx=5)
        ttk.Label(outlier_frame, text="Akcja:").grid(row=0, column=2, padx=5, pady=2)
        ttk.Combobox(
            outlier_frame,
            textvariable=self.outlier_action_choice,
            values=["flag", "clip", "drop", "keep"],
            state="readonly",
            width=8,
        ).grid(row=0, column=3, padx=5)
        ttk.Button(outlier_frame, text="Sprawdź", command=self.on_check_outliers).grid(row=0, column=4, padx=5)
        ttk.Button(outlier_frame, text="Zastosuj", command=self.on_apply_outliers).grid(row=0, column=5, padx=5)

        profile_frame = ttk.LabelFrame(parent, text="Profil danych", padding=10)
        profile_frame.pack(side="top", fill="both", expand=True, pady=5)

        ttk.Label(profile_frame, textvariable=self.summary_text).pack(side="top", anchor="w", pady=(0, 5))

        column_names = ("column", "dtype", "missing", "missing_pct", "unique")
        self.profile_table = ttk.Treeview(profile_frame, columns=column_names, show="headings", height=5)
        self.profile_table.heading("column", text="Kolumna")
        self.profile_table.heading("dtype", text="Typ")
        self.profile_table.heading("missing", text="Braki")
        self.profile_table.heading("missing_pct", text="Braki %")
        self.profile_table.heading("unique", text="Unikalne")
        self.profile_table.pack(side="top", fill="both", expand=True)

        statistics_frame = ttk.LabelFrame(parent, text="Statystyki opisowe (kolumny liczbowe)", padding=10)
        statistics_frame.pack(side="top", fill="both", expand=True, pady=5)

        statistics_columns = ("column",) + STATISTIC_NAMES
        self.statistics_table = ttk.Treeview(
            statistics_frame, columns=statistics_columns, show="headings", height=5
        )
        self.statistics_table.heading("column", text="Kolumna")
        self.statistics_table.column("column", width=120)
        for name in STATISTIC_NAMES:
            self.statistics_table.heading(name, text=name)
            self.statistics_table.column(name, width=80, anchor="e")
        self.statistics_table.pack(side="top", fill="both", expand=True)

    def build_plots_tab(self, parent: ttk.Frame) -> None:
        plot_controls = ttk.Frame(parent)
        plot_controls.pack(side="top", fill="x", pady=5)

        ttk.Label(plot_controls, text="Typ:").pack(side="left", padx=5)
        ttk.Combobox(
            plot_controls,
            textvariable=self.plot_type_choice,
            values=["histogram", "box", "scatter", "bar", "correlation"],
            state="readonly",
            width=12,
        ).pack(side="left", padx=5)

        ttk.Label(plot_controls, text="Kolumna X:").pack(side="left", padx=5)
        self.plot_x_combo = ttk.Combobox(
            plot_controls, textvariable=self.plot_x_choice, state="readonly", width=18
        )
        self.plot_x_combo.pack(side="left", padx=5)

        ttk.Label(plot_controls, text="Oś Y (scatter):").pack(side="left", padx=5)
        self.plot_y_combo = ttk.Combobox(
            plot_controls, textvariable=self.plot_y_choice, state="readonly", width=18
        )
        self.plot_y_combo.pack(side="left", padx=5)

        ttk.Button(plot_controls, text="Rysuj wykres", command=self.on_draw_plot).pack(
            side="left", padx=10
        )

        ttk.Button(plot_controls, text="Zapisz wykres", command=self.on_save_plot).pack(
            side="left", padx=5
        )

        self.plot_area = ttk.Frame(parent)
        self.plot_area.pack(side="top", fill="both", expand=True)

    def build_log_tab(self, parent: ttk.Frame) -> None:
        log_columns = ("time", "operation", "params", "before", "after", "affected")
        self.log_table = ttk.Treeview(parent, columns=log_columns, show="headings")
        self.log_table.heading("time", text="Czas")
        self.log_table.heading("operation", text="Operacja")
        self.log_table.heading("params", text="Parametry")
        self.log_table.heading("before", text="Przed")
        self.log_table.heading("after", text="Po")
        self.log_table.heading("affected", text="Dotknięte")
        self.log_table.column("time", width=130)
        self.log_table.column("operation", width=170)
        self.log_table.column("params", width=420)
        self.log_table.column("before", width=60, anchor="e")
        self.log_table.column("after", width=60, anchor="e")
        self.log_table.column("affected", width=80, anchor="e")
        self.log_table.pack(side="top", fill="both", expand=True)
        
    def on_open_file(self) -> None:
        path_text = filedialog.askopenfilename(
            title="Wybierz plik CSV",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")],
        )
        if path_text == "":
            return  # użytkownik anulował

        try:
            new_session = DataSession.from_csv(Path(path_text))
        except StudioError as error:
            messagebox.showerror("Błąd wczytywania", str(error))
            self.status_text.set("Nie udało się wczytać pliku.")
            return

        self.session = new_session
        self.file_text.set(Path(path_text).name)
        row_count = len(new_session.raw)
        column_count = len(new_session.raw.columns)
        self.status_text.set(f"Wczytano {row_count} rekordów i {column_count} kolumn.")
        self.clear_plot()
        self.refresh_all()

    def refresh_profile(self) -> None:
        """Czyści tabelę profilu i wypełnia ją na podstawie bieżących danych sesji."""
        for item_id in self.profile_table.get_children():
            self.profile_table.delete(item_id)

        if self.session is None:
            self.summary_text.set("")
            return

        profile = build_profile(self.session.current)
        self.summary_text.set(
            f"Rekordy: {profile.row_count} | Kolumny: {profile.column_count} | "
            f"Pełne duplikaty: {profile.duplicate_count}"
        )

        for _, row in profile.columns.iterrows():
            self.profile_table.insert(
                "",
                "end",
                values=(
                    row["column"],
                    row["dtype"],
                    row["missing"],
                    row["missing_pct"],
                    row["unique"],
                ),
            )

    def refresh_column_choices(self) -> None:
        """Odświeża listy kolumn po zmianie zbioru danych."""
        if self.session is None:
            self.column_combo["values"] = []
            self.column_choice.set("")
            self.plot_x_combo["values"] = []
            self.plot_x_choice.set("")
            self.plot_y_combo["values"] = []
            self.plot_y_choice.set("")
            return

        column_names = list(self.session.current.columns)
        self.column_combo["values"] = column_names
        self.plot_x_combo["values"] = column_names
        self.plot_y_combo["values"] = column_names

        if self.column_choice.get() not in column_names:
            if len(column_names) > 0:
                self.column_choice.set(column_names[0])
            else:
                self.column_choice.set("")

        if self.plot_x_choice.get() not in column_names:
            if len(column_names) > 0:
                self.plot_x_choice.set(column_names[0])
            else:
                self.plot_x_choice.set("")

        if self.plot_y_choice.get() not in column_names:
            if len(column_names) > 1:
                self.plot_y_choice.set(column_names[1])
            elif len(column_names) > 0:
                self.plot_y_choice.set(column_names[0])
            else:
                self.plot_y_choice.set("")

    def refresh_all(self) -> None:
        self.refresh_profile()
        self.refresh_statistics()
        self.refresh_preview()
        self.refresh_column_choices()
        self.refresh_log()

    def require_session(self) -> bool:
        if self.session is None:
            messagebox.showwarning("Brak danych", "Najpierw wczytaj plik CSV.")
            return False
        return True

    def on_drop_duplicates(self) -> None:
        if not self.require_session():
            return
        try:
            removed_count = drop_exact_duplicates(self.session)
        except StudioError as error:
            messagebox.showerror("Błąd czyszczenia", str(error))
            return
        self.status_text.set(f"Usunięto duplikaty: {removed_count}.")
        self.refresh_all()

    def on_handle_missing(self) -> None:
        if not self.require_session():
            return

        column_name = self.column_choice.get()
        strategy = self.strategy_choice.get()
        columns = []
        if column_name != "":
            columns.append(column_name)

        try:
            if strategy == "drop":
                affected_count = drop_rows_with_missing(self.session, columns)
                self.status_text.set(f"Usunięto rekordy z brakami: {affected_count}.")
            elif strategy == "constant":
                affected_count = fill_missing_with_constant(
                    self.session, columns, self.constant_text.get()
                )
                self.status_text.set(f"Wypełniono braki stałą: {affected_count}.")
            else:
                affected_count = fill_missing_with_statistic(self.session, columns, strategy)
                self.status_text.set(f"Wypełniono braki ({strategy}): {affected_count}.")
        except StudioError as error:
            messagebox.showerror("Błąd czyszczenia", str(error))
            return

        self.refresh_all()

    def on_reset(self) -> None:
        if not self.require_session():
            return
        self.session.reset()
        self.status_text.set("Przywrócono dane surowe.")
        self.refresh_all()

    def parse_optional_number(self, text: str, label: str) -> float | None:
        """Zamienia tekst z pola na liczbę. Puste pole oznacza brak granicy."""
        cleaned_text = text.strip().replace(",", ".")
        if cleaned_text == "":
            return None
        try:
            return float(cleaned_text)
        except ValueError:
            raise ValidationError(
                f"{label} '{text}' nie jest liczbą. Wpisz liczbę, na przykład 0 albo 12.5."
            )

    def read_range_limits(self) -> tuple[float | None, float | None]:
        minimum = self.parse_optional_number(self.minimum_text.get(), "Minimum")
        maximum = self.parse_optional_number(self.maximum_text.get(), "Maksimum")
        return minimum, maximum

    def read_iqr_factor(self) -> float:
        factor = self.parse_optional_number(self.iqr_factor_text.get(), "Współczynnik")
        if factor is None:
            raise ValidationError("Nie podano współczynnika IQR. Wpisz na przykład 1.5.")
        return factor

    def on_check_range(self) -> None:
        if not self.require_session():
            return
        try:
            minimum, maximum = self.read_range_limits()
            found_count = report_out_of_range(
                self.session, self.column_choice.get(), minimum, maximum
            )
        except StudioError as error:
            messagebox.showerror("Błąd reguły zakresu", str(error))
            return
        self.status_text.set(
            f"Reguła zakresu: znaleziono {found_count} wartości poza zakresem. Dane bez zmian."
        )

        self.refresh_log()

    def on_apply_range(self) -> None:
        if not self.require_session():
            return
        try:
            minimum, maximum = self.read_range_limits()
            column_name = self.column_choice.get()
            action = self.range_action_choice.get()
            report_out_of_range(self.session, column_name, minimum, maximum)
            found_count = self.session.audit_log[-1].params["found"]
            if found_count == 0:
                self.status_text.set("Nic nie zmieniono: brak wartości poza zakresem.")
                return
            confirmed = messagebox.askyesno(
                "Potwierdzenie",
                f"Znaleziono {found_count} wartości poza zakresem.\n"
                f"Zastosować akcję '{action}' na kolumnie '{column_name}'?",
            )
            if not confirmed:
                self.status_text.set("Anulowano. Dane bez zmian.")
                return
            affected_count = apply_range_rule(self.session, column_name, minimum, maximum, action)
        except StudioError as error:
            messagebox.showerror("Błąd reguły zakresu", str(error))
            return
        self.status_text.set(f"Reguła zakresu ({action}): zmieniono {affected_count}.")
        self.refresh_all()

    def on_check_outliers(self) -> None:
        if not self.require_session():
            return
        try:
            factor = self.read_iqr_factor()
            mask = find_outliers_iqr(self.session, self.column_choice.get(), factor)
        except StudioError as error:
            messagebox.showerror("Błąd wykrywania", str(error))
            return
        self.status_text.set(
            f"IQR (współczynnik {factor}): znaleziono {int(mask.sum())} wartości odstających. "
            "Dane bez zmian."
        )

    def on_apply_outliers(self) -> None:
        if not self.require_session():
            return
        try:
            factor = self.read_iqr_factor()
            column_name = self.column_choice.get()
            action = self.outlier_action_choice.get()
            found_count = int(find_outliers_iqr(self.session, column_name, factor).sum())
            confirmed = messagebox.askyesno(
                "Potwierdzenie",
                f"Metoda IQR (współczynnik {factor}) znalazła {found_count} wartości odstających "
                f"w kolumnie '{column_name}'.\nZastosować akcję '{action}'?",
            )
            if not confirmed:
                self.status_text.set("Anulowano. Dane bez zmian.")
                return
            handle_outliers(self.session, column_name, action, factor)
        except StudioError as error:
            messagebox.showerror("Błąd wykrywania", str(error))
            return
        self.status_text.set(
            f"IQR ({action}): znaleziono {found_count} wartości odstających."
        )
        self.refresh_all()

    def refresh_log(self) -> None:
        """Czyści tabelę dziennika i wypełnia ją wpisami z sesji."""
        for item_id in self.log_table.get_children():
            self.log_table.delete(item_id)

        if self.session is None:
            return

        for entry in self.session.audit_log:
            self.log_table.insert(
                "",
                "end",
                values=(
                    entry.timestamp,
                    entry.operation,
                    str(entry.params),
                    entry.rows_before,
                    entry.rows_after,
                    entry.affected,
                ),
            )

    def build_figure(self) -> Figure:
        """Wybiera funkcję wykresu na podstawie wyboru użytkownika."""
        plot_type = self.plot_type_choice.get()
        x_column = self.plot_x_choice.get()
        y_column = self.plot_y_choice.get()

        if plot_type == "correlation":
            return correlation_figure(self.session)

        if x_column == "":
            raise ValidationError("Nie wybrano kolumny. Wybierz kolumnę z listy 'Kolumna X'.")

        if plot_type == "histogram":
            return histogram_figure(self.session, x_column)
        if plot_type == "box":
            return box_plot_figure(self.session, x_column)
        if plot_type == "bar":
            return bar_figure(self.session, x_column)
        if plot_type == "scatter":
            return scatter_figure(self.session, x_column, y_column)

        raise ValidationError(f"Nieznany typ wykresu '{plot_type}'.")

    def show_figure(self, figure: Figure) -> None:
        """Osadza wykres w oknie i usuwa poprzedni canvas."""
        self.clear_plot()

        canvas = FigureCanvasTkAgg(figure, master=self.plot_area)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.current_figure = figure
        self.plot_canvas = canvas

    def clear_plot(self) -> None:
        if self.plot_canvas is not None:
            self.plot_canvas.get_tk_widget().destroy()
        self.plot_canvas = None
        self.current_figure = None

    def on_draw_plot(self) -> None:
        if not self.require_session():
            return
        try:
            figure = self.build_figure()
        except StudioError as error:
            messagebox.showerror("Nie można narysować wykresu", str(error))
            self.status_text.set("Wykres zablokowany: niepoprawny wybór kolumn.")
            return

        self.show_figure(figure)
        self.status_text.set(f"Narysowano wykres: {self.plot_type_choice.get()}.")

    def on_save_csv(self) -> None:
        if not self.require_session():
            return
        path_text = filedialog.asksaveasfilename(
            title="Zapisz oczyszczony CSV",
            defaultextension=".csv",
            initialfile="cleaned.csv",
            filetypes=[("Pliki CSV", "*.csv")],
        )
        if path_text == "":
            return
        try:
            saved = save_cleaned_csv(self.session, path_text)
        except StudioError as error:
            messagebox.showerror("Błąd zapisu", str(error))
            return
        self.status_text.set(f"Zapisano dane: {saved.name}")

    def on_save_report(self) -> None:
        if not self.require_session():
            return
        path_text = filedialog.asksaveasfilename(
            title="Zapisz raport zmian",
            defaultextension=".txt",
            initialfile="audit_report.txt",
            filetypes=[("Tekst", "*.txt"), ("CSV", "*.csv")],
        )
        if path_text == "":
            return
        try:
            saved = save_audit_report(self.session, path_text)
        except StudioError as error:
            messagebox.showerror("Błąd zapisu", str(error))
            return
        self.status_text.set(f"Zapisano raport: {saved.name}")

    def on_save_plot(self) -> None:
        if self.current_figure is None:
            messagebox.showwarning("Brak wykresu", "Najpierw narysuj wykres.")
            return
        path_text = filedialog.asksaveasfilename(
            title="Zapisz wykres",
            defaultextension=".png",
            initialfile="wykres.png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
        )
        if path_text == "":
            return
        try:
            saved = save_figure(self.current_figure, path_text)
        except StudioError as error:
            messagebox.showerror("Błąd zapisu", str(error))
            return
        self.status_text.set(f"Zapisano wykres: {saved.name}")

    def build_preview_tab(self, parent: ttk.Frame) -> None:
        self.preview_info_text = tk.StringVar(value="")
        ttk.Label(parent, textvariable=self.preview_info_text).pack(side="top", anchor="w", pady=(0, 5))

        table_frame = ttk.Frame(parent)
        table_frame.pack(side="top", fill="both", expand=True)

        self.preview_table = ttk.Treeview(table_frame, show="headings")
        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.preview_table.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.preview_table.xview)
        self.preview_table.configure(
            yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set
        )

        vertical_scroll.pack(side="right", fill="y")
        horizontal_scroll.pack(side="bottom", fill="x")
        self.preview_table.pack(side="left", fill="both", expand=True)

    def refresh_preview(self) -> None:
        """Pokazuje pierwsze rekordy bieżących danych. Kolumny tworzone dynamicznie."""
        for item_id in self.preview_table.get_children():
            self.preview_table.delete(item_id)

        if self.session is None:
            self.preview_table["columns"] = ()
            self.preview_info_text.set("")
            return

        frame = self.session.current
        column_names = [str(name) for name in frame.columns]

        self.preview_table["columns"] = column_names
        for name in column_names:
            self.preview_table.heading(name, text=name)
            self.preview_table.column(name, width=110, anchor="w")

        shown = frame.head(PREVIEW_ROW_LIMIT)
        for _, row in shown.iterrows():
            values = []
            for value in row:
                if pd.isna(value):
                    values.append("")
                else:
                    values.append(str(value))
            self.preview_table.insert("", "end", values=values)

        self.preview_info_text.set(
            f"Pokazano {len(shown)} z {len(frame)} rekordów (puste pole = brak wartości)."
        )

    def refresh_statistics(self) -> None:
        for item_id in self.statistics_table.get_children():
            self.statistics_table.delete(item_id)

        if self.session is None:
            return

        statistics = build_numeric_statistics(self.session.current)
        if statistics.empty:
            return

        for _, row in statistics.iterrows():
            values = [row["column"]]
            for name in STATISTIC_NAMES:
                values.append(round(float(row[name]), 3))
            self.statistics_table.insert("", "end", values=values)

def run_app() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()