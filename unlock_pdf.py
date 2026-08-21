"""
PDF Password Remover
A portable Windows app to strip passwords from PDF files in bulk.
Requires: customtkinter, pikepdf
Build with: pyinstaller PDF_Unlocker.spec
"""

import os
import sys
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    import pikepdf
except ImportError:
    if getattr(sys, "frozen", False):
        raise
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pikepdf"])
    import pikepdf

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("System")   # follows Windows light/dark setting
ctk.set_default_color_theme("blue")

ACCENT      = "#2563EB"
ACCENT_DARK = "#1D4ED8"
RED         = "#EF4444"
RED_DARK    = "#DC2626"
GRAY_BTN    = ("gray80", "gray30")
GRAY_HOVER  = ("gray70", "gray40")
GRAY_TEXT   = ("black", "white")


def _resource_path(*parts: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "lbarsic.PDFPasswordRemover"
        )
    except Exception:
        pass


class AutoHideScrollableFrame(ctk.CTkScrollableFrame):
    """Scrollable frame whose scrollbar is shown only when content overflows."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bar_visible = True
        self._syncing = False
        self.bind("<Configure>", self._sync_scrollbar, add="+")
        self._parent_canvas.bind("<Configure>", self._sync_scrollbar, add="+")
        self.after_idle(self._sync_scrollbar)

    def _create_grid(self):
        super()._create_grid()
        if not getattr(self, "_bar_visible", True):
            try:
                self._scrollbar.grid_remove()
            except Exception:
                pass

    def _sync_scrollbar(self, event=None):
        if self._syncing:
            return
        self._syncing = True
        try:
            canvas = self._parent_canvas
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox is not None:
                canvas.configure(scrollregion=bbox)
            y0, y1 = canvas.yview()
            if canvas.winfo_height() <= 1 or y1 <= y0:
                need = False
            else:
                need = (y1 - y0) < 0.999
            if need and not self._bar_visible:
                self._scrollbar.grid()
                self._bar_visible = True
            elif not need and self._bar_visible:
                self._scrollbar.grid_remove()
                canvas.yview_moveto(0)
                self._bar_visible = False
        except Exception:
            pass
        finally:
            self._syncing = False


# ── App ────────────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PDF Password Remover")
        self.geometry("700x640")
        self.minsize(560, 520)
        self._apply_icon()

        # State
        self.selected_files: list[str] = []
        self.file_widgets:  dict[str, ctk.CTkFrame] = {}
        self.output_dir    = ctk.StringVar()
        self.password_var  = ctk.StringVar()
        self.show_password = False
        self._running      = False

        self._build_ui()
        self.bind("<Configure>", self._sync_body_scroll, add="+")
        self.after_idle(self._sync_body_scroll)

    def _apply_icon(self):
        ico = _resource_path("assets", "app.ico")
        png = _resource_path("assets", "app.png")
        if os.path.isfile(ico):
            try:
                self.iconbitmap(ico)
            except Exception:
                pass
        if os.path.isfile(png):
            try:
                self._icon_photo = tk.PhotoImage(file=png)
                self.iconphoto(True, self._icon_photo)
            except Exception:
                pass
        # CustomTkinter can reset the window icon after init.
        self.after(200, self._reapply_iconbitmap)

    def _reapply_iconbitmap(self):
        ico = _resource_path("assets", "app.ico")
        if os.path.isfile(ico):
            try:
                self.iconbitmap(ico)
            except Exception:
                pass
        if getattr(self, "_icon_photo", None) is not None:
            try:
                self.iconphoto(True, self._icon_photo)
            except Exception:
                pass

    def _sync_body_scroll(self, event=None):
        try:
            self.body._sync_scrollbar()
        except Exception:
            pass

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray93", "gray13"))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="🔓  PDF Password Remover",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 2))

        ctk.CTkLabel(
            hdr, text="Strip encryption from one or many PDF files at once.",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

    def _build_body(self):
        body = AutoHideScrollableFrame(self, corner_radius=0, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self.body = body

        # ── Section 1 : Files ──────────────────────────────────────────────────
        self._section_label(body, "PDF FILES", row=0)

        # File list container
        self.files_box = ctk.CTkFrame(body, fg_color=("gray88", "gray17"), corner_radius=10)
        self.files_box.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.files_box.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.files_box,
            text="No files selected yet — click 'Add PDF Files' below.",
            text_color="gray", font=ctk.CTkFont(size=12),
        )
        self.empty_label.grid(row=0, column=0, pady=22)

        # Buttons row
        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 4))

        ctk.CTkButton(
            btn_row, text="+ Add PDF Files", command=self.add_files,
            height=36, corner_radius=8, width=150,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Clear All", command=self.clear_all,
            height=36, corner_radius=8, width=100,
            fg_color=GRAY_BTN, hover_color=GRAY_HOVER, text_color=GRAY_TEXT,
        ).pack(side="left")

        # ── Section 2 : Password ───────────────────────────────────────────────
        self._section_label(body, "PDF PASSWORD", row=3)

        pwd_row = ctk.CTkFrame(body, fg_color="transparent")
        pwd_row.grid(row=4, column=0, sticky="ew", padx=20)
        pwd_row.grid_columnconfigure(0, weight=1)

        self.pwd_entry = ctk.CTkEntry(
            pwd_row,
            placeholder_text="Enter the password used to open the PDF…",
            textvariable=self.password_var,
            show="●", height=42, font=ctk.CTkFont(size=13),
        )
        self.pwd_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.toggle_btn = ctk.CTkButton(
            pwd_row, text="Show", width=74, height=42,
            fg_color=GRAY_BTN, hover_color=GRAY_HOVER, text_color=GRAY_TEXT,
            command=self.toggle_password,
        )
        self.toggle_btn.grid(row=0, column=1)

        # ── Section 3 : Output folder ──────────────────────────────────────────
        self._section_label(body, "OUTPUT FOLDER", row=5)

        out_row = ctk.CTkFrame(body, fg_color="transparent")
        out_row.grid(row=6, column=0, sticky="ew", padx=20)
        out_row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            out_row,
            placeholder_text="Where to save the unlocked PDFs…",
            textvariable=self.output_dir,
            height=42, font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            out_row, text="Browse…", width=84, height=42,
            fg_color=GRAY_BTN, hover_color=GRAY_HOVER, text_color=GRAY_TEXT,
            command=self.browse_output,
        ).grid(row=0, column=1)

        # ── Progress ───────────────────────────────────────────────────────────
        self.status_var = ctk.StringVar(value="Ready")
        ctk.CTkLabel(
            body, textvariable=self.status_var,
            text_color="gray", font=ctk.CTkFont(size=12),
        ).grid(row=7, column=0, pady=(20, 4))

        self.progress = ctk.CTkProgressBar(body, height=10, corner_radius=6)
        self.progress.grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.progress.set(0)

    def _build_footer(self):
        foot = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray93", "gray13"))
        foot.grid(row=2, column=0, sticky="ew")
        foot.grid_columnconfigure(0, weight=1)

        self.start_btn = ctk.CTkButton(
            foot,
            text="🔓   Remove Passwords",
            command=self.start,
            height=50, corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.start_btn.grid(row=0, column=0, padx=20, pady=14, sticky="ew")

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _section_label(parent, text, row):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray", anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(22, 6))

    @staticmethod
    def _human_size(n: int) -> str:
        if n < 1024:
            return f"{n} B"
        if n < 1024 ** 2:
            return f"{n / 1024:.1f} KB"
        return f"{n / 1024 ** 2:.1f} MB"

    # ── File management ────────────────────────────────────────────────────────

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        added = 0
        for p in paths:
            if p not in self.selected_files:
                self.selected_files.append(p)
                self._add_file_row(p)
                added += 1
        if added:
            self.empty_label.grid_remove()
        self.after_idle(self._sync_body_scroll)

    def _add_file_row(self, path: str):
        idx = len(self.file_widgets)
        row = ctk.CTkFrame(
            self.files_box,
            fg_color=("gray93", "gray23"),
            corner_radius=7,
        )
        row.grid(row=idx, column=0, sticky="ew", padx=8, pady=4)
        row.grid_columnconfigure(1, weight=1)
        self.files_box.grid_columnconfigure(0, weight=1)

        # PDF icon
        ctk.CTkLabel(row, text="📄", font=ctk.CTkFont(size=18), width=36).grid(
            row=0, column=0, padx=(10, 4), pady=8,
        )
        # Filename
        ctk.CTkLabel(
            row, text=os.path.basename(path),
            font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=8)
        # Size badge
        ctk.CTkLabel(
            row,
            text=self._human_size(os.path.getsize(path)),
            font=ctk.CTkFont(size=11), text_color="gray",
        ).grid(row=0, column=2, padx=10)
        # Remove button
        ctk.CTkButton(
            row, text="✕", width=30, height=30,
            fg_color="transparent",
            hover_color=("gray75", "gray35"),
            text_color=("gray50", "gray60"),
            command=lambda p=path: self.remove_file(p),
        ).grid(row=0, column=3, padx=(0, 6))

        self.file_widgets[path] = row

    def remove_file(self, path: str):
        if path in self.file_widgets:
            self.file_widgets[path].destroy()
            del self.file_widgets[path]
            self.selected_files.remove(path)
            # Re-grid remaining rows
            for i, (p, w) in enumerate(self.file_widgets.items()):
                w.grid(row=i, column=0, sticky="ew", padx=8, pady=4)
        if not self.selected_files:
            self.empty_label.grid()
        self.after_idle(self._sync_body_scroll)

    def clear_all(self):
        for w in self.file_widgets.values():
            w.destroy()
        self.file_widgets.clear()
        self.selected_files.clear()
        self.empty_label.grid()
        self.after_idle(self._sync_body_scroll)

    # ── UI interactions ────────────────────────────────────────────────────────

    def toggle_password(self):
        self.show_password = not self.show_password
        self.pwd_entry.configure(show="" if self.show_password else "●")
        self.toggle_btn.configure(text="Hide" if self.show_password else "Show")

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir.set(folder)

    # ── Processing ─────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return

        # Validate
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please add at least one PDF file.")
            return
        out = self.output_dir.get().strip()
        if not out:
            messagebox.showwarning("No Output Folder", "Please choose an output folder.")
            return
        if not os.path.isdir(out):
            messagebox.showerror("Invalid Folder", f"Folder does not exist:\n{out}")
            return

        if not self.password_var.get():
            if not messagebox.askyesno(
                "No Password",
                "No password was entered.\n\nProceed anyway?\n"
                "(Files that aren't password-protected will still be saved to the output folder.)",
            ):
                return

        self._running = True
        self.start_btn.configure(state="disabled", text="⏳  Processing…")
        self.progress.set(0)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        files    = self.selected_files.copy()
        password = self.password_var.get()
        out_dir  = self.output_dir.get().strip()
        total    = len(files)
        success, failed = [], []

        for i, path in enumerate(files):
            name = os.path.basename(path)
            self._set_status(f"Processing {i + 1}/{total}: {name}")
            self._set_progress(i / total)

            try:
                dest = self._unique_path(out_dir, name)
                with pikepdf.open(path, password=password) as pdf:
                    pdf.save(dest)
                success.append(name)
            except pikepdf.PasswordError:
                failed.append((name, "Wrong password"))
            except pikepdf.PdfError as e:
                failed.append((name, f"PDF error: {e}"))
            except Exception as e:
                failed.append((name, str(e)))

        self._set_progress(1.0)
        self._set_status(
            f"Done — {len(success)}/{total} file(s) unlocked successfully."
            if not failed else
            f"Completed with errors — {len(success)}/{total} succeeded."
        )
        self.after(0, lambda: self._finish(success, failed, out_dir))

    @staticmethod
    def _unique_path(folder: str, filename: str) -> str:
        dest = os.path.join(folder, filename)
        if not os.path.exists(dest):
            return dest
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(folder, f"{base}_unlocked_{counter}{ext}")
            counter += 1
        return dest

    def _finish(self, success: list, failed: list, out_dir: str):
        self._running = False
        self.start_btn.configure(state="normal", text="🔓   Remove Passwords")

        lines = [f"✅  {len(success)} file(s) successfully unlocked."]
        if success:
            lines.append(f"📁  Saved to: {out_dir}")
        if failed:
            lines.append(f"\n❌  {len(failed)} file(s) failed:")
            for name, reason in failed:
                lines.append(f"   • {name}\n     → {reason}")

        (messagebox.showinfo if not failed else messagebox.showwarning)(
            "Done", "\n".join(lines)
        )

    # ── Thread-safe setters ────────────────────────────────────────────────────

    def _set_status(self, text: str):
        self.after(0, lambda: self.status_var.set(text))

    def _set_progress(self, value: float):
        self.after(0, lambda: self.progress.set(value))


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _windows_app_id()
    app = App()
    app.mainloop()
