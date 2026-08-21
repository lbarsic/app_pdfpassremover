# PDF Password Remover

A portable Windows app that strips passwords from PDF files in bulk.
No installation required — build once, then copy a single `.exe` anywhere.

---

## Files

| File | Purpose |
|------|---------|
| `unlock_pdf.py` | Application source code |
| `requirements.txt` | Python dependencies |
| `PDF_Unlocker.spec` | PyInstaller spec (one-file, windowed) |
| `build.bat` | One-click Windows build script |

`build/`, `build_env/`, and `dist/` are generated locally and are not committed.

---

## How to Build the Executable

**Requirements:** Python 3.9 or newer ([python.org](https://python.org))

1. Place the repo files in the same folder.
2. Double-click `build.bat`.
3. The script will automatically:
   - Create an isolated virtual environment
   - Install `customtkinter`, `pikepdf`, and `pyinstaller`
   - Build `dist\PDF_Unlocker.exe`
4. Copy `PDF_Unlocker.exe` anywhere you like — it's fully self-contained.

> **First build takes ~2–3 minutes** (downloading libraries). Subsequent builds are faster.

---

## Run from source

```bash
pip install -r requirements.txt
python unlock_pdf.py
```

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
- The source is pure Python — you can inspect, modify, and rebuild freely.
- The `.exe` bundles everything; no Python installation is needed on the target machine.
- No installers, registry keys, or hardcoded paths — the executable is portable.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails | Make sure Python is on your PATH; re-run `build.bat` |
| "Wrong password" error | Double-check the password; note it's case-sensitive |
| Antivirus flags the `.exe` | PyInstaller-built executables are sometimes flagged falsely; add an exclusion or build on the target machine |
| App won't start | Try running from a terminal (`PDF_Unlocker.exe`) to see any error output |
