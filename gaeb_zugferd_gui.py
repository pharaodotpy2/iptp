#!/usr/bin/env python3
"""Simple Tkinter GUI for GAEB/X83/X84/ZUGFeRD workflow."""

from __future__ import annotations

import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gaeb_zugferd_tool import parse_gaeb_xml, write_gaeb_x8x, create_zugferd_pdf


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GAEB + ZUGFeRD GUI")
        self.geometry("800x520")

        self.input_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.cwd() / "out"))
        self.status_var = tk.StringVar(value="Bereit")

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        # input
        ttk.Label(frame, text="GAEB Input XML:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.input_var, width=78).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Datei wählen", command=self.pick_input).grid(row=1, column=1, sticky="ew")

        # output dir
        ttk.Label(frame, text="Output Ordner:").grid(row=2, column=0, pady=(12, 0), sticky="w")
        ttk.Entry(frame, textvariable=self.output_dir_var, width=78).grid(row=3, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Ordner wählen", command=self.pick_output_dir).grid(row=3, column=1, sticky="ew")

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=2, pady=14, sticky="ew")

        ttk.Button(btns, text="GAEB prüfen", command=self.on_parse).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="X83 erzeugen", command=self.on_x83).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="X84 erzeugen", command=self.on_x84).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="ZUGFeRD PDF", command=self.on_pdf).pack(side=tk.LEFT)

        ttk.Label(frame, text="Ergebnis / Daten:").grid(row=5, column=0, sticky="w")
        self.output = tk.Text(frame, wrap="word", height=18)
        self.output.grid(row=6, column=0, columnspan=2, sticky="nsew")

        status = ttk.Label(frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(6, weight=1)

    def pick_input(self) -> None:
        path = filedialog.askopenfilename(
            title="GAEB XML auswählen",
            filetypes=[("XML", "*.xml"), ("Alle Dateien", "*.*")],
        )
        if path:
            self.input_var.set(path)

    def pick_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Output Ordner auswählen")
        if path:
            self.output_dir_var.set(path)

    def _validate(self) -> tuple[Path, Path]:
        input_path = Path(self.input_var.get().strip())
        output_dir = Path(self.output_dir_var.get().strip())
        if not input_path.exists():
            raise ValueError("Bitte eine gültige GAEB XML Datei wählen.")
        output_dir.mkdir(parents=True, exist_ok=True)
        return input_path, output_dir

    def _run_bg(self, action_name: str, fn) -> None:
        def worker() -> None:
            self.status_var.set(f"{action_name} läuft …")
            try:
                fn()
                self.status_var.set(f"{action_name} abgeschlossen")
            except Exception as exc:  # UI error path
                self.status_var.set(f"Fehler bei {action_name}")
                self.output.insert(tk.END, "\n" + traceback.format_exc() + "\n")
                self.output.see(tk.END)
                messagebox.showerror("Fehler", str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def on_parse(self) -> None:
        input_path, _ = self._validate()

        def task() -> None:
            data = parse_gaeb_xml(input_path)
            self.output.delete("1.0", tk.END)
            self.output.insert(
                tk.END,
                (
                    f"Rechnung: {data.invoice_number}\n"
                    f"Datum: {data.issue_date}\n"
                    f"Verkäufer: {data.seller_name}\n"
                    f"Käufer: {data.buyer_name}\n"
                    f"Währung: {data.currency}\n"
                    f"Positionen: {len(data.items)}\n"
                    f"Gesamt: {data.grand_total}\n\n"
                ),
            )
            for item in data.items:
                self.output.insert(
                    tk.END,
                    f"- {item.line_id}: {item.description} | {item.quantity} {item.unit} x {item.unit_price} = {item.total}\n",
                )

        self._run_bg("GAEB prüfen", task)

    def on_x83(self) -> None:
        input_path, output_dir = self._validate()

        def task() -> None:
            data = parse_gaeb_xml(input_path)
            out = output_dir / "x83.xml"
            write_gaeb_x8x(data, out, "X83")
            self.output.insert(tk.END, f"\nX83 erzeugt: {out}\n")
            self.output.see(tk.END)

        self._run_bg("X83 erzeugen", task)

    def on_x84(self) -> None:
        input_path, output_dir = self._validate()

        def task() -> None:
            data = parse_gaeb_xml(input_path)
            out = output_dir / "x84.xml"
            write_gaeb_x8x(data, out, "X84")
            self.output.insert(tk.END, f"\nX84 erzeugt: {out}\n")
            self.output.see(tk.END)

        self._run_bg("X84 erzeugen", task)

    def on_pdf(self) -> None:
        input_path, output_dir = self._validate()

        def task() -> None:
            data = parse_gaeb_xml(input_path)
            out = output_dir / "rechnung.pdf"
            create_zugferd_pdf(data, out)
            self.output.insert(tk.END, f"\nZUGFeRD PDF erzeugt: {out}\n")
            self.output.see(tk.END)

        self._run_bg("ZUGFeRD PDF", task)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
