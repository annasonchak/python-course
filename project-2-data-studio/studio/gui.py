"""Interfejs graficzny. Nie zawiera logiki biznesowej, tylko wywołuje moduły studio."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from studio.errors import StudioError
from studio.profiling import build_profile
from studio.session import DataSession

class App:
    """Główne okno aplikacji. Cały stan sesji jest polem tego obiektu."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.session: DataSession | None = None

        self.root.title("Studio jakości i wizualizacji danych")
        self.root.geometry("900x600")

        self.status_text = tk.StringVar(value="Wybierz plik CSV, aby rozpocząć.")
        self.file_text = tk.StringVar(value="Brak wczytanego pliku")

        self.summary_text = tk.StringVar(value="")
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

        profile_frame = ttk.LabelFrame(self.root, text="Profil danych", padding=10)
        profile_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

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
        self.refresh_profile()

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

def run_app() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()