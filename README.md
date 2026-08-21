# PDF Password Remover

A portable Windows app that strips passwords from PDF files in bulk.

**No install. No Python. No build.** Download the `.exe`, copy it anywhere, double-click.

---

## Download

**[PDF_Unlocker.exe](https://github.com/lbarsic/app_pdfpassremover/releases/latest/download/PDF_Unlocker.exe)** — latest portable build (Windows x64)

Or grab it from the [Releases](https://github.com/lbarsic/app_pdfpassremover/releases) page.

Copy the file to a USB stick, a folder on your desktop, anywhere. It does not write to the registry or require admin rights.

---

## How to Use the App

1. **Add PDF Files** — Click "+ Add PDF Files" and select one or more `.pdf` files.
2. **Enter Password** — Type the password used to open/protect those PDFs.
   - Click "Show" to reveal what you're typing.
   - All selected files must share the same password.
     For different passwords, run the app in separate batches.
3. **Choose Output Folder** — Click "Browse…" to pick where unlocked PDFs are saved.
4. **Remove Passwords** — Click the blue button. Progress is shown live.
5. A summary popup lists which files succeeded and which (if any) failed.

Unlocked files are saved with the **same filename** in the output folder.
If a file with that name already exists, `_unlocked_1`, `_unlocked_2`, etc. is appended automatically.

---

## Notes

- The app uses **pikepdf** (backed by the battle-tested `qpdf` library) for reliable decryption of AES-128, AES-256, and RC4-encrypted PDFs.
- The `.exe` bundles everything; no Python installation is needed on the target machine.
- No installers, registry keys, or hardcoded paths — the executable is portable.
- Antivirus tools sometimes flag PyInstaller apps. That is a false positive; add an exclusion if needed.

---

## For developers (optional)

Source is in this repo if you want to change or rebuild the app. You do **not** need this to use it.

```bash
pip install -r requirements.txt
python unlock_pdf.py
```

To rebuild the portable `.exe` on Windows: double-click `build.bat` (Python 3.9+ on PATH). Output is `dist\PDF_Unlocker.exe`.
