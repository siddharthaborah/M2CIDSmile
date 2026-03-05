"""
M2CIDSmile Tool — Molecule Information Fetcher
Fetches PubChem CIDs and Canonical SMILES for a list of molecules.

Modern GUI built with CustomTkinter.
"""

import os
import sys
import csv
import json
import ssl
import threading
import time
import webbrowser
from io import StringIO
from tkinter import filedialog, messagebox
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Windows DPI awareness — must be set before any tkinter import
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Auto-install customtkinter if missing (only when running as script)
# ---------------------------------------------------------------------------
try:
    import customtkinter as ctk
except ImportError:
    if not getattr(sys, "frozen", False):
        print("Installing customtkinter...")
        os.system(f'"{sys.executable}" -m pip install customtkinter')
        import customtkinter as ctk
    else:
        raise


# ---------------------------------------------------------------------------
# SSL context — works in both normal and PyInstaller-frozen mode
# ---------------------------------------------------------------------------
def _create_ssl_context():
    """Create an SSL context that works on any Windows PC.

    PyInstaller bundles may not find the system certificate store, so
    we try certifi first, then system certs, then a permissive fallback.
    """
    # 1. Try certifi (bundled with the .exe)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    # 2. Try the system default
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        pass

    # 3. Last resort — unverified (still HTTPS, just no cert check)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


SSL_CTX = _create_ssl_context()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
APP_TITLE = "M2CIDSmile Tool"
VERSION = "2.0"
SAMPLE_MOLECULES = [
    "Aspirin", "Caffeine", "Glucose", "Paracetamol",
    "Ibuprofen", "Quercetin", "Curcumin", "Resveratrol",
]


# ============================================================================
# PubChem API Helper
# ============================================================================
class PubChemFetcher:
    """Handles PubChem REST API requests with retries."""

    @staticmethod
    def _fetch_json(url: str, retries: int = 3):
        """Fetch JSON from a URL with retries. Returns dict or None."""
        for attempt in range(retries + 1):
            try:
                req = Request(url, headers={"Accept": "application/json",
                                            "User-Agent": "M2CIDSmile-Tool/2.0"})
                with urlopen(req, timeout=20, context=SSL_CTX) as resp:
                    return json.loads(resp.read().decode())
            except HTTPError as e:
                if e.code == 404:
                    return None  # molecule not found
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return None
            except (URLError, OSError, json.JSONDecodeError):
                if attempt < retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                return None
        return None

    @classmethod
    def check_connectivity(cls) -> bool:
        """Return True if PubChem API is reachable."""
        try:
            req = Request(f"{PUBCHEM_BASE}/compound/name/water/cids/JSON",
                          headers={"User-Agent": "M2CIDSmile-Tool/2.0"})
            with urlopen(req, timeout=10, context=SSL_CTX) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def fetch(cls, molecule_name: str) -> dict:
        """Return {molecule, cid, smiles} for a given molecule name."""
        encoded = quote(molecule_name, safe="")
        cid = None
        smiles = None

        # Step 1 — CID
        data = cls._fetch_json(f"{PUBCHEM_BASE}/compound/name/{encoded}/cids/JSON")
        if data:
            cids = data.get("IdentifierList", {}).get("CID", [])
            cid = cids[0] if cids else None

        # Step 2 — SMILES
        if cid:
            data = cls._fetch_json(
                f"{PUBCHEM_BASE}/compound/cid/{cid}/property/CanonicalSMILES/JSON"
            )
            if data:
                props = (data.get("PropertyTable", {}).get("Properties") or [{}])[0]
                smiles = props.get("CanonicalSMILES") or props.get("ConnectivitySMILES")

        return {"molecule": molecule_name, "cid": cid, "smiles": smiles}


# ============================================================================
# Modern Scrollable Table Widget
# ============================================================================
class ResultsTable(ctk.CTkScrollableFrame):
    """A scrollable results table with alternating row colours."""

    HEADER_COLS = ("#", "Molecule", "PubChem CID", "SMILES", "Status")
    COL_WIDTHS  = (40, 150, 110, 320, 80)

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._rows: list[list[ctk.CTkLabel]] = []
        self._build_header()

    def _build_header(self):
        for col, (text, w) in enumerate(zip(self.HEADER_COLS, self.COL_WIDTHS)):
            lbl = ctk.CTkLabel(self, text=text, width=w, anchor="w",
                               font=ctk.CTkFont(size=12, weight="bold"),
                               text_color=("#475569", "#94a3b8"))
            lbl.grid(row=0, column=col, padx=(6, 2), pady=(4, 8), sticky="w")

    def clear(self):
        for row_labels in self._rows:
            for lbl in row_labels:
                lbl.destroy()
        self._rows.clear()

    def add_row(self, index: int, molecule: str, cid, smiles, found: bool):
        r = len(self._rows) + 1
        bg = ("#f8fafc", "#1a2332") if r % 2 == 0 else "transparent"
        vals = [
            str(index),
            molecule,
            str(cid) if cid else "—",
            smiles if smiles else "—",
            "✓ Found" if found else "✗ N/A",
        ]
        status_color = ("#16a34a", "#4ade80") if found else ("#dc2626", "#f87171")
        row_labels = []
        for col, (text, w) in enumerate(zip(vals, self.COL_WIDTHS)):
            color = status_color if col == 4 else None
            lbl = ctk.CTkLabel(
                self, text=text, width=w, anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12) if col in (2, 3) else ctk.CTkFont(size=12),
                text_color=color,
                fg_color=bg,
                corner_radius=4,
            )
            lbl.grid(row=r, column=col, padx=(6, 2), pady=1, sticky="w")
            row_labels.append(lbl)
        self._rows.append(row_labels)


# ============================================================================
# Main Application
# ============================================================================
class M2CIDSmileApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window ──
        self.title(f"{APP_TITLE}  v{VERSION}")
        self.geometry("980x720")
        self.minsize(780, 550)
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # ── Window icon ──
        self._set_icon()

        # ── State ──
        self._molecules: list[str] = []
        self._results: list[dict] = []
        self._processing = False
        self._cancel = False

        # ── Build UI ──
        self._build_header()
        self._build_notebook()
        self._build_input_tab()
        self._build_results_tab()
        self._build_footer()

    # ------------------------------------------------------------------- icon
    def _set_icon(self):
        """Set the window icon from app_icon.ico."""
        try:
            # When frozen by PyInstaller, files are in _MEIPASS
            base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            ico_path = os.path.join(base, 'app_icon.ico')
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
                # Also set for alt-tab on Windows
                self.after(200, lambda: self.iconbitmap(ico_path))
        except Exception:
            pass  # Not critical — fall back to default icon

    # ------------------------------------------------------------------ header
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("white", "#1e293b"), corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Logo
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        ctk.CTkLabel(title_frame, text="⬡",
                     font=ctk.CTkFont(size=28), text_color=("#6366f1", "#818cf8")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_frame, text="M2CIDSmile",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkLabel(title_frame, text="Molecule Information Fetcher",
                     font=ctk.CTkFont(size=12),
                     text_color=("#64748b", "#94a3b8")).pack(side="left", padx=(12, 0))

        # Theme toggle
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)
        self._theme_btn = ctk.CTkButton(
            btn_frame, text="🌙 Dark", width=80, height=30,
            font=ctk.CTkFont(size=12), command=self._toggle_theme,
            fg_color=("gray85", "gray25"), text_color=("gray30", "gray80"),
            hover_color=("gray75", "gray35"),
        )
        self._theme_btn.pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="? Help", width=70, height=30,
            font=ctk.CTkFont(size=12), command=self._show_help,
            fg_color=("gray85", "gray25"), text_color=("gray30", "gray80"),
            hover_color=("gray75", "gray35"),
        ).pack(side="right", padx=4)

    def _toggle_theme(self):
        mode = ctk.get_appearance_mode()
        new = "Light" if mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new)
        self._theme_btn.configure(text="☀️ Light" if new == "Dark" else "🌙 Dark")

    # --------------------------------------------------------------- notebook
    def _build_notebook(self):
        self._tabview = ctk.CTkTabview(self, anchor="nw")
        self._tabview.pack(fill="both", expand=True, padx=16, pady=(8, 4))
        self._tabview.add("Input")
        self._tabview.add("Results")

    # --------------------------------------------------------------- footer
    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent", height=28)
        footer.pack(fill="x", side="bottom", padx=16, pady=(0, 6))
        ctk.CTkLabel(
            footer,
            text="Developed by Dr. Arabinda Ghosh, Department of Molecular Biology & Bioinformatics, Tripura University",
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#94a3b8"),
        ).pack(side="bottom")

    # ----------------------------------------------------------- input tab
    def _build_input_tab(self):
        tab = self._tabview.tab("Input")

        # ── Mode selector ──
        mode_frame = ctk.CTkFrame(tab, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, 8))
        self._mode_var = ctk.StringVar(value="manual")
        ctk.CTkRadioButton(mode_frame, text="Type molecule names",
                           variable=self._mode_var, value="manual",
                           command=self._switch_mode).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(mode_frame, text="Upload CSV file",
                           variable=self._mode_var, value="csv",
                           command=self._switch_mode).pack(side="left")

        # ── Manual input ──
        self._manual_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self._manual_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self._manual_frame, text="Enter one molecule name per line:",
                     font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        self._text_input = ctk.CTkTextbox(self._manual_frame, font=ctk.CTkFont(family="Consolas", size=13),
                                          corner_radius=8, border_width=1,
                                          border_color=("gray70", "gray30"))
        self._text_input.pack(fill="both", expand=True)
        self._text_input.bind("<KeyRelease>", lambda e: self._update_count())

        # ── CSV input (hidden initially) ──
        self._csv_frame = ctk.CTkFrame(tab, fg_color="transparent")

        csv_inner = ctk.CTkFrame(self._csv_frame, fg_color=("gray95", "#0f172a"),
                                 corner_radius=12, border_width=2,
                                 border_color=("gray75", "gray35"))
        csv_inner.pack(fill="both", expand=True, pady=10)

        csv_content = ctk.CTkFrame(csv_inner, fg_color="transparent")
        csv_content.place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(csv_content, text="📄", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(csv_content, text="Click to select a CSV file",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(csv_content, text='CSV must contain a column named "molecule"',
                     font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")).pack()
        ctk.CTkButton(csv_content, text="Browse Files", width=140, height=36,
                      command=self._browse_csv).pack(pady=16)
        self._csv_label = ctk.CTkLabel(csv_content, text="", font=ctk.CTkFont(size=12),
                                       text_color=("#16a34a", "#4ade80"))
        self._csv_label.pack()

        # ── Bottom bar ──
        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.pack(fill="x", pady=(12, 0))

        left_btns = ctk.CTkFrame(bottom, fg_color="transparent")
        left_btns.pack(side="left")

        ctk.CTkButton(left_btns, text="⚡ Load Sample Data", width=150, height=34,
                      fg_color=("gray85", "gray25"), text_color=("gray30", "gray80"),
                      hover_color=("gray75", "gray35"),
                      command=self._load_sample).pack(side="left", padx=(0, 8))

        ctk.CTkButton(left_btns, text="📥 Download Template", width=155, height=34,
                      fg_color=("gray85", "gray25"), text_color=("gray30", "gray80"),
                      hover_color=("gray75", "gray35"),
                      command=self._download_template).pack(side="left")

        self._count_label = ctk.CTkLabel(bottom, text="0 molecules",
                                         font=ctk.CTkFont(size=12),
                                         text_color=("gray50", "gray60"))
        self._count_label.pack(side="left", padx=20)

        self._fetch_btn = ctk.CTkButton(
            bottom, text="▶  Fetch Molecule Data", width=220, height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#6366f1", "#818cf8"), hover_color=("#4f46e5", "#6366f1"),
            command=self._start_processing,
        )
        self._fetch_btn.pack(side="right")

    # --------------------------------------------------------- results tab
    def _build_results_tab(self):
        tab = self._tabview.tab("Results")

        # ── Summary cards ──
        self._summary_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self._summary_frame.pack(fill="x", pady=(0, 10))
        self._summary_labels: dict[str, ctk.CTkLabel] = {}
        cards = [
            ("Total", "#6366f1", "total"),
            ("Found", "#16a34a", "found"),
            ("Not Found", "#dc2626", "notfound"),
            ("Time", "#3b82f6", "time"),
        ]
        for text, color, key in cards:
            card = ctk.CTkFrame(self._summary_frame, corner_radius=10,
                                fg_color=("gray95", "#1a2332"), border_width=1,
                                border_color=("gray80", "gray30"))
            card.pack(side="left", expand=True, fill="x", padx=4)
            val_lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=26, weight="bold"),
                                   text_color=color)
            val_lbl.pack(pady=(10, 0))
            ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray60")).pack(pady=(0, 10))
            self._summary_labels[key] = val_lbl

        # ── Progress bar (hidden until processing) ──
        self._progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self._progress_bar = ctk.CTkProgressBar(self._progress_frame, width=400, height=14,
                                                 corner_radius=7,
                                                 progress_color=("#6366f1", "#818cf8"))
        self._progress_bar.set(0)
        self._progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self._progress_label = ctk.CTkLabel(self._progress_frame, text="0 / 0",
                                             font=ctk.CTkFont(size=12))
        self._progress_label.pack(side="left", padx=(0, 12))
        self._cancel_btn = ctk.CTkButton(self._progress_frame, text="Cancel", width=80, height=30,
                                          fg_color=("#dc2626", "#b91c1c"),
                                          hover_color=("#b91c1c", "#991b1b"),
                                          command=self._cancel_processing)
        self._cancel_btn.pack(side="right")
        # Initially hidden — packed in position but immediately forgotten
        self._progress_frame.pack(fill="x", pady=(0, 8))
        self._progress_frame.pack_forget()

        # ── Action bar ──
        action_bar = ctk.CTkFrame(tab, fg_color="transparent")
        action_bar.pack(fill="x", pady=(0, 6))

        self._search_entry = ctk.CTkEntry(action_bar, placeholder_text="Search results...",
                                           width=250, height=34)
        self._search_entry.pack(side="left")
        self._search_entry.bind("<KeyRelease>", lambda e: self._filter_table())

        self._filter_var = ctk.StringVar(value="all")
        for text, val in [("All", "all"), ("Found", "found"), ("Not Found", "notfound")]:
            ctk.CTkRadioButton(action_bar, text=text, variable=self._filter_var,
                               value=val, command=self._filter_table,
                               font=ctk.CTkFont(size=12)).pack(side="left", padx=10)

        ctk.CTkButton(action_bar, text="📥 Download CSV", width=130, height=34,
                      fg_color=("#6366f1", "#818cf8"), hover_color=("#4f46e5", "#6366f1"),
                      command=self._download_results).pack(side="right", padx=(8, 0))
        ctk.CTkButton(action_bar, text="🔄 New Search", width=120, height=34,
                      fg_color=("gray85", "gray25"), text_color=("gray30", "gray80"),
                      hover_color=("gray75", "gray35"),
                      command=self._new_search).pack(side="right")

        # ── Table ──
        self._table = ResultsTable(tab, corner_radius=10,
                                   fg_color=("white", "#111827"),
                                   border_width=1, border_color=("gray80", "gray30"))
        self._table.pack(fill="both", expand=True)

    # ============================================================ actions

    def _switch_mode(self):
        if self._mode_var.get() == "manual":
            self._csv_frame.pack_forget()
            self._manual_frame.pack(fill="both", expand=True)
            # Move the bottom bar below
            for w in self._manual_frame.master.winfo_children():
                if w not in (self._manual_frame, self._csv_frame):
                    w.pack_configure()
        else:
            self._manual_frame.pack_forget()
            self._csv_frame.pack(fill="both", expand=True)
        self._update_count()

    def _browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fields = [h.strip().lower() for h in (reader.fieldnames or [])]
                if "molecule" not in fields:
                    messagebox.showerror("Invalid CSV",
                                         'The CSV file must contain a column named "molecule".')
                    return
                names = []
                for row in reader:
                    # case-insensitive column lookup
                    val = None
                    for k, v in row.items():
                        if k.strip().lower() == "molecule":
                            val = v.strip()
                            break
                    if val:
                        names.append(val)
            if not names:
                messagebox.showwarning("Empty file", "No molecule names found in the CSV.")
                return
            self._molecules = names
            self._csv_label.configure(
                text=f"✓ Loaded {len(names)} molecule(s) from {os.path.basename(path)}")
            self._update_count()
        except Exception as ex:
            messagebox.showerror("Error", f"Could not read file:\n{ex}")

    def _update_count(self):
        mols = self._get_molecules()
        self._count_label.configure(text=f"{len(mols)} molecule{'s' if len(mols) != 1 else ''}")

    def _get_molecules(self) -> list[str]:
        if self._mode_var.get() == "csv":
            return self._molecules
        text = self._text_input.get("1.0", "end").strip()
        if not text:
            return []
        return [l.strip() for l in text.split("\n") if l.strip()]

    def _load_sample(self):
        self._mode_var.set("manual")
        self._switch_mode()
        self._text_input.delete("1.0", "end")
        self._text_input.insert("1.0", "\n".join(SAMPLE_MOLECULES))
        self._update_count()

    def _download_template(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="molecules_template.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["molecule"])
            for m in SAMPLE_MOLECULES[:5]:
                writer.writerow([m])
        messagebox.showinfo("Saved", f"Template saved to:\n{path}")

    # --------------------------------------------------------- processing
    def _start_processing(self):
        mols = self._get_molecules()
        if not mols:
            messagebox.showwarning("No data", "Please enter or upload molecule names first.")
            return
        if self._processing:
            return

        # Check internet connectivity before starting
        self._fetch_btn.configure(state="disabled", text="Checking connection...")
        self.update_idletasks()

        def _check_and_start():
            if not PubChemFetcher.check_connectivity():
                self.after(0, lambda: (
                    self._fetch_btn.configure(state="normal",
                                             text="▶  Fetch Molecule Data"),
                    messagebox.showerror(
                        "No Internet Connection",
                        "Cannot reach PubChem servers.\n\n"
                        "Please check your internet connection and try again.\n\n"
                        "If you are behind a firewall or proxy, ensure access\n"
                        "to pubchem.ncbi.nlm.nih.gov is allowed."
                    )
                ))
                return
            self.after(0, self._begin_processing, mols)

        threading.Thread(target=_check_and_start, daemon=True).start()

    def _begin_processing(self, mols):
        self._processing = True
        self._cancel = False
        self._results.clear()

        # Switch to results tab
        self._tabview.set("Results")
        self._table.clear()

        # Show progress bar
        self._progress_frame.pack(fill="x", pady=(0, 8), after=self._summary_frame)
        self._progress_bar.set(0)
        self._progress_label.configure(text=f"0 / {len(mols)}")

        # Reset summaries
        for k in self._summary_labels:
            self._summary_labels[k].configure(text="0")

        self._fetch_btn.configure(state="disabled")

        # Run in background thread
        thread = threading.Thread(target=self._process_worker, args=(mols,), daemon=True)
        thread.start()

    def _process_worker(self, molecules: list[str]):
        start = time.time()
        found = 0
        not_found = 0

        for i, name in enumerate(molecules):
            if self._cancel:
                break

            result = PubChemFetcher.fetch(name)
            self._results.append(result)

            ok = bool(result["cid"] and result["smiles"])
            if ok:
                found += 1
            else:
                not_found += 1

            # Update UI from main thread
            idx = i + 1
            self.after(0, self._update_progress, idx, len(molecules),
                       found, not_found, result, start)

            # Rate limiting
            if i < len(molecules) - 1:
                time.sleep(0.5)

        elapsed = time.time() - start
        self.after(0, self._processing_done, found, not_found, elapsed)

    def _update_progress(self, current, total, found, not_found, result, start):
        pct = current / total
        self._progress_bar.set(pct)
        self._progress_label.configure(text=f"{current} / {total}")

        elapsed = time.time() - start
        self._summary_labels["total"].configure(text=str(current))
        self._summary_labels["found"].configure(text=str(found))
        self._summary_labels["notfound"].configure(text=str(not_found))
        self._summary_labels["time"].configure(text=self._fmt_time(elapsed))

        ok = bool(result["cid"] and result["smiles"])
        self._table.add_row(current, result["molecule"], result["cid"], result["smiles"], ok)

    def _processing_done(self, found, not_found, elapsed):
        self._processing = False
        self._progress_frame.pack_forget()
        self._fetch_btn.configure(state="normal", text="▶  Fetch Molecule Data")
        self._summary_labels["time"].configure(text=self._fmt_time(elapsed))

        if self._cancel:
            messagebox.showinfo("Cancelled", "Processing was cancelled.")
        else:
            messagebox.showinfo(
                "Complete",
                f"Processed {found + not_found} molecules.\n"
                f"Found: {found}  |  Not found: {not_found}\n"
                f"Time: {self._fmt_time(elapsed)}"
            )

    def _cancel_processing(self):
        self._cancel = True

    def _new_search(self):
        self._tabview.set("Input")
        self._table.clear()
        self._results.clear()
        for k in self._summary_labels:
            self._summary_labels[k].configure(text="0")
        self._search_entry.delete(0, "end")

    # --------------------------------------------------------- filter & search
    def _filter_table(self):
        search = self._search_entry.get().strip().lower()
        filt = self._filter_var.get()

        self._table.clear()
        idx = 0
        for r in self._results:
            ok = bool(r["cid"] and r["smiles"])

            # Filter
            if filt == "found" and not ok:
                continue
            if filt == "notfound" and ok:
                continue

            # Search
            text = f"{r['molecule']} {r['cid'] or ''} {r['smiles'] or ''}".lower()
            if search and search not in text:
                continue

            idx += 1
            self._table.add_row(idx, r["molecule"], r["cid"], r["smiles"], ok)

    # --------------------------------------------------------- download results
    def _download_results(self):
        if not self._results:
            messagebox.showwarning("No results", "No results to download.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="molecule-output.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["CID", "Molecule", "SMILES"])
            for r in self._results:
                writer.writerow([r["cid"] or "", r["molecule"], r["smiles"] or ""])
        messagebox.showinfo("Saved", f"Results saved to:\n{path}")

    # --------------------------------------------------------- help
    def _show_help(self):
        win = ctk.CTkToplevel(self)
        win.title("How to Use M2CIDSmile Tool")
        win.geometry("560x520")
        win.transient(self)
        win.grab_set()
        win.after(100, win.lift)

        frame = ctk.CTkScrollableFrame(win, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        help_text = """
What does this tool do?

M2CIDSmile fetches PubChem Compound IDs (CID) and Canonical SMILES strings for molecules using the PubChem database API. SMILES is a text representation of a molecule's chemical structure.


Option 1: Type Manually

  1.  Select "Type molecule names"
  2.  Enter one molecule name per line
  3.  Click "Fetch Molecule Data"


Option 2: Upload CSV

  1.  Select "Upload CSV file"
  2.  Browse for a CSV file with a column named "molecule"
  3.  Click "Fetch Molecule Data"


CSV File Format Example

    molecule
    Aspirin
    Caffeine
    Glucose
    Paracetamol


Where to get molecule names?

  •  KNApSAcK — knapsackfamily.com/KNApSAcK/
  •  IMPPAT — cb.imsc.res.in/imppat/
  •  PubChem — pubchem.ncbi.nlm.nih.gov
"""
        ctk.CTkLabel(frame, text=help_text.strip(), justify="left", anchor="nw",
                     wraplength=500, font=ctk.CTkFont(size=13)).pack(fill="both")

        ctk.CTkButton(win, text="Close", width=100, command=win.destroy).pack(pady=(0, 12))

    # --------------------------------------------------------- utility
    @staticmethod
    def _fmt_time(seconds: float) -> str:
        s = int(seconds)
        if s < 60:
            return f"{s}s"
        return f"{s // 60}m {s % 60}s"


# ============================================================================
# Entry Point
# ============================================================================
def main():
    try:
        app = M2CIDSmileApp()
        app.mainloop()
    except Exception as e:
        # Show a user-friendly error dialog instead of crashing silently
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "M2CIDSmile Error",
                f"An unexpected error occurred:\n\n{e}\n\n"
                f"Please ensure you have an internet connection\n"
                f"and try again."
            )
            root.destroy()
        except Exception:
            print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
