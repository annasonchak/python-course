"""Interfejs graficzny. Nie zawiera logiki biznesowej, tylko wywołuje moduły studio."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

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

from studio.errors import StudioError
from studio.profiling import build_profile
from studio.session import DataSession
from studio.errors import StudioError, ValidationError

class App:
    """Główne okno aplikacji. Cały stan sesji jest polem tego obiektu."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.session: DataSession | None = None

        self.root.title("Studio jakości i wizualizacji danych")
        self.root.geometry("1000x800")

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

        self.build_widgets()

    def build_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side="top", fill="x")

        open_button = ttk.Button(top_frame, text="Wybierz plik CSV", command=self.on_open_file)
        open_button.pack(side="left")

        file_label = ttk.Label(top_frame, textvariable=self.file_text)
        file_label.pack(side="left", padx=10)

        status_bar = ttk.Label(self.root, textvariable=self.status_text, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

        cleaning_frame = ttk.LabelFrame(self.root, text="Czyszczenie", padding=10)
        cleaning_frame.pack(side="top", fill="x", padx=10, pady=5)

        duplicates_button = ttk.Button(
            cleaning_frame, text="Usuń duplikaty", command=self.on_drop_duplicates
        )
        duplicates_button.grid(row=0, column=0, padx=5, pady=2)

        reset_button = ttk.Button(cleaning_frame, text="Resetuj dane", command=self.on_reset)
        reset_button.grid(row=0, column=1, padx=5, pady=2)

        column_label = ttk.Label(cleaning_frame, text="Kolumna:")
        column_label.grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.column_combo = ttk.Combobox(
            cleaning_frame, textvariable=self.column_choice, state="readonly", width=20
        )
        self.column_combo.grid(row=1, column=1, padx=5, pady=2)

        strategy_label = ttk.Label(cleaning_frame, text="Strategia braków:")
        strategy_label.grid(row=1, column=2, sticky="e", padx=5, pady=2)
        strategy_combo = ttk.Combobox(
            cleaning_frame,
            textvariable=self.strategy_choice,
            values=["drop", "constant", "mean", "median", "mode"],
            state="readonly",
            width=12,
        )
        strategy_combo.grid(row=1, column=3, padx=5, pady=2)

        constant_label = ttk.Label(cleaning_frame, text="Stała:")
        constant_label.grid(row=1, column=4, sticky="e", padx=5, pady=2)
        constant_entry = ttk.Entry(cleaning_frame, textvariable=self.constant_text, width=10)
        constant_entry.grid(row=1, column=5, padx=5, pady=2)

        missing_button = ttk.Button(
            cleaning_frame, text="Uzupełnij braki", command=self.on_handle_missing
        )
        missing_button.grid(row=1, column=6, padx=5, pady=2)

        range_frame = ttk.LabelFrame(self.root, text="Reguła zakresu (dla kolumny wybranej wyżej)", padding=10)
        range_frame.pack(side="top", fill="x", padx=10, pady=5)

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

        outlier_frame = ttk.LabelFrame(self.root, text="Wartości odstające IQR (dla kolumny wybranej wyżej)", padding=10)
        outlier_frame.pack(side="top", fill="x", padx=10, pady=5)

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

        profile_frame = ttk.LabelFrame(self.root, text="Profil danych", padding=10)
        profile_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        log_frame = ttk.LabelFrame(self.root, text="Dziennik zmian", padding=10)
        log_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        log_columns = ("time", "operation", "params", "before", "after", "affected")
        self.log_table = ttk.Treeview(log_frame, columns=log_columns, show="headings", height=5)
        self.log_table.heading("time", text="Czas")
        self.log_table.heading("operation", text="Operacja")
        self.log_table.heading("params", text="Parametry")
        self.log_table.heading("before", text="Przed")
        self.log_table.heading("after", text="Po")
        self.log_table.heading("affected", text="Dotknięte")
        self.log_table.column("time", width=130)
        self.log_table.column("operation", width=170)
        self.log_table.column("params", width=320)
        self.log_table.column("before", width=60, anchor="e")
        self.log_table.column("after", width=60, anchor="e")
        self.log_table.column("affected", width=80, anchor="e")
        self.log_table.pack(side="top", fill="both", expand=True)

        summary_label = ttk.Label(profile_frame, textvariable=self.summary_text)
        summary_label.pack(side="top", anchor="w", pady=(0, 5))

        column_names = ("column", "dtype", "missing", "missing_pct", "unique")
        self.profile_table = ttk.Treeview(profile_frame, columns=column_names, show="headings", height=10)
        self.profile_table.heading("column", text="Kolumna")
        self.profile_table.heading("dtype", text="Typ")
        self.profile_table.heading("missing", text="Braki")
        self.profile_table.heading("missing_pct", text="Braki %")
        self.profile_table.heading("unique", text="Unikalne")
        self.profile_table.pack(side="top", fill="both", expand=True)

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
        """Odświeża listę kolumn po zmianie zbioru danych."""
        if self.session is None:
            self.column_combo["values"] = []
            self.column_choice.set("")
            return

        column_names = list(self.session.current.columns)
        self.column_combo["values"] = column_names

        if self.column_choice.get() not in column_names:
            if len(column_names) > 0:
                self.column_choice.set(column_names[0])
            else:
                self.column_choice.set("")

    def refresh_all(self) -> None:
        self.refresh_profile()
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

def run_app() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()