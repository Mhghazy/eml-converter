# ✉️ Maildir → EML Bulk Converter (V3.3)

![Version](https://img.shields.io/badge/version-3.3-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A robust, multi-threaded desktop application designed to perform bulk conversions of **Maildir** mailboxes into standard, easily accessible **.eml** files. Built with Python, Tkinter, and the native `mailbox` library, it features an elegant dark-mode UI, automatic metadata sanitization, and timestamp preservation.

---

## 🌟 Key Features

- **Direct Mailbox Parsing**: Automatically scans and identifies Maildir folder structures (`cur`, `new`, `tmp`) across complex directory trees.
- **Smart File Renaming**: Extracts email headers (`Date`, `From`, `Subject`) to generate clean, highly descriptive, and OS-safe filenames (e.g., `00001_2026-05-16_14-30_sender_subject.eml`).
- **Timestamp Preservation**: Restores original file creation and modification timestamps (`st_atime`, `st_mtime`) on the output `.eml` files for accurate archival auditing.
- **Asynchronous & Multi-Threaded**: Runs conversion workloads on a dedicated background thread, keeping the GUI responsive and providing real-time progress bar updates.
- **Fault-Tolerant Execution**: Gracefully catches and logs corrupt or malformed messages without interrupting the bulk conversion process.
- **Standalone Executable Ready**: Bundled with a custom PyInstaller `.spec` configuration and Windows version info manifest for building a professional `.exe` with icon support.

---

## 🏗️ Technical Architecture

The application is structured into three decoupled layers:

```
┌────────────────────────────────────────────────────────┐
│                   GUI Layer (Tkinter)                  │
│    App (Main Window) | ScrolledText Log | Help Modal   │
└───────────────────────────┬────────────────────────────┘
                            │ (Asynchronous Events)
                            ▼
┌────────────────────────────────────────────────────────┐
│                Threading & Event Bridge                │
│    threading.Thread (Background Worker Execution)      │
└───────────────────────────┬────────────────────────────┘
                            │ (File I/O & Parsing)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Core Converter & I/O Engine              │
│    mailbox.Maildir | os.scandir | email.utils          │
└────────────────────────────────────────────────────────┘
```

### 1. GUI Layer (`App`)
- Inherits from `tk.Tk` and utilizes `ttk.Progressbar` and `scrolledtext.ScrolledText`.
- Implements a modern dark-themed palette (`#1a1a2e` background, `#0f3460` accent, `#e94560` highlights).
- Uses `after(0, callback)` thread-safe UI scheduling to handle log updates and progress increments dispatched from the worker thread.

### 2. Core Converter Engine (`convert_all`)
- **Discovery**: `find_all_maildirs()` traverses the root path using high-performance `os.scandir` to locate valid Maildir directories containing `cur` subfolders.
- **Ingestion**: Iterates through each identified Maildir using `mailbox.Maildir(..., create=False)`.
- **Extraction & Sanitization**: Uses `parsedate_to_datetime` to standardize RFC 2822 date strings into ISO-like filenames. `sanitize()` strips invalid Windows filesystem characters (`\/:*?"<>|`) and truncates lengths to prevent `PathTooLong` OS exceptions.
- **Preservation**: Leverages `os.stat` and `os.utime` to mirror file metadata from the source Maildir message to the newly created `.eml` binary file.

---

## 🚀 Installation & Development Setup

### Prerequisites
- **Python 3.8+** installed on Windows.
- Standard library dependencies (`tkinter`, `mailbox`, `email`, `threading`).

### Running from Source
Clone the repository and execute the main Python script directly:

```powershell
git clone https://github.com/Mhghazy/eml-converter.git
cd eml-converter
python emlconverter.py
```

---

## 📦 Building the Standalone Executable (`.exe`)

The project includes a pre-configured PyInstaller specification (`emlconverter.spec`) and a Windows version info manifest (`version.txt`) to generate a single-file executable with embedded icons and metadata.

### Build Instructions

1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Run PyInstaller using the provided `.spec` file:
   ```powershell
   pyinstaller emlconverter.spec
   ```
3. Locate your compiled executable in the `dist/` directory:
   ```powershell
   .\dist\emlconverter.exe
   ```

---

## 📖 User Guide

1. **Launch the Application**: Open `emlconverter.exe` (or run `emlconverter.py`).
2. **Select Source Folder**: Click **Browse...** next to *Source Mailbox Folder* and select the parent folder containing your Maildir structure (e.g., `user.name` directory containing `INBOX`, `Sent`, etc.).
3. **Select Output Folder**: Click **Browse...** next to *Output Folder* and choose an empty destination folder where the `.eml` files will be exported.
4. **Start Conversion**: Click the red **Start Conversion** button.
5. **Monitor Progress**: The progress bar and real-time log will show exactly which folder and email is currently being processed. Once complete, a summary dialog will appear.

---

## 🛡️ License & Author

- **Author**: Mahmoud Hamdy
- **Copyright**: Copyright (c) 2026 Mahmoud Hamdy
- **License**: MIT License. Free for personal and commercial use.
