# PDF to MD Converter

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
</p>

A cross-platform desktop application that converts PDF files to clean Markdown. Built with a restrained, two-theme UI, drag-and-drop support, and native OS file dialogs for a seamless user experience.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0%2B-lightgrey)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.28%2B-orange)
![PyWebView](https://img.shields.io/badge/pywebview-5.0%2B-green)

## Screenshots

<table>
<tr>
<td width="50%"><img src="screenshots/splash.png" alt="PDF2MD startup splash screen"><br><sub>Startup splash</sub></td>
<td width="50%"><img src="screenshots/warm-theme.png" alt="PDF2MD in the Warm Editorial theme"><br><sub>Warm Editorial theme</sub></td>
</tr>
<tr>
<td width="50%"><img src="screenshots/dark-theme.png" alt="PDF2MD in the Pro Dark theme with a completed conversion"><br><sub>Pro Dark theme</sub></td>
<td width="50%"><img src="screenshots/exit-confirmation.png" alt="Exit confirmation dialog"><br><sub>Exit confirmation</sub></td>
</tr>
</table>

## Features

- 📄 **Drag & Drop Upload** — Intuitive file upload with visual feedback
- ⚡ **Batch Conversion** — Convert multiple PDFs simultaneously with real-time progress tracking
- 🌗 **Warm / Dark Themes** — Two considered themes, switchable in-app and remembered across launches
- 🔁 **Smart Deduplication** — Prevents duplicate file uploads in the queue
- 💾 **Native Save Dialog** — Choose any folder to save your Markdown files (falls back to a normal browser download outside the desktop shell)
- 🚪 **Exit Confirmation** — Confirms before closing so you don't lose an in-progress queue
- 🖥️ **Cross-Platform** — Native desktop app for Windows, macOS, and Linux
- 📦 **Standalone Executable** — Package as a single distributable binary

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/pdf2md.git
cd pdf2md

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the App

```bash
python desktop.py
```

## Building Standalone Executables

Package the app for your current platform:

```bash
pyinstaller pdf2md.spec
```

The executable will be generated in the `dist/` folder:
- **Windows:** `dist/PDF2MD.exe`
- **macOS:** `dist/PDF2MD`
- **Linux:** `dist/PDF2MD`

### Platform-Specific Notes

#### Windows
```bash
pyinstaller pdf2md.spec
```
Distribute `dist/PDF2MD.exe`. No additional dependencies needed.

#### macOS
```bash
pyinstaller pdf2md.spec
```
For distribution outside your machine, you may need to:
1. Code-sign the application
2. Notarize with Apple
3. Create a proper `.app` bundle structure

#### Linux
```bash
pyinstaller pdf2md.spec
```
The binary should work on most modern Linux distributions. For broader compatibility, consider building on an older distro (e.g., Ubuntu 20.04) using Docker or a VM.

## Usage

1. **Launch** the app with `python desktop.py`
2. **Upload** PDF files by dragging them into the drop zone or clicking "Browse Files"
3. **Convert** — Click "Convert All" to start batch conversion
4. **Download** — After conversion completes, click the download icon to save each `.md` file to your preferred location
5. **Clear** — Remove all files from the queue with "Clear Queue"

## Project Structure

```
pdf2md/
├── app.py                 # Flask backend (upload, conversion, download API)
├── converter.py           # PDF to Markdown conversion logic (PyMuPDF)
├── desktop.py             # Desktop app entry point (PyWebView wrapper)
├── pdf2md.spec            # PyInstaller build configuration
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Warm / Dark themed UI
├── screenshots/           # README screenshots
├── uploads/               # Temporary PDF uploads (auto-created)
├── outputs/               # Converted Markdown files (auto-created)
└── dist/                  # Built executables (generated)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask 3.0+ |
| **PDF Processing** | PyMuPDF 1.28+ |
| **Desktop Wrapper** | PyWebView 5.0+ |
| **Packaging** | PyInstaller 6.0+ |
| **Frontend** | HTML5, CSS3 (custom properties, animations), vanilla JavaScript |

## Configuration

### Output Location

By default, converted `.md` files are saved to:
```
<project-root>/outputs/<filename>.md
```

The actual conversion happens in the `outputs/` folder, but when you click **Download**, you can choose any destination folder via the native OS save dialog.

### Duplicate Handling

- **Client-side:** Duplicate filenames in the queue are blocked with an error toast
- **Server-side:** If multiple files share the same name, outputs are auto-incremented: `file.md`, `file_1.md`, `file_2.md`

## Troubleshooting

### `ModuleNotFoundError: No module named 'flask'` (or `pymupdf`, `webview`)
Make sure you activated the virtual environment:
```bash
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

### `ImportError: DLL load failed while importing _extra`
This is a PyMuPDF dependency issue on Windows. Fix it by upgrading PyMuPDF:
```bash
pip install --upgrade PyMuPDF
```

### PyInstaller build fails
Make sure you're using Python 3.9+. Some packages may require additional hooks. Check the PyInstaller logs for missing modules.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Dark/light theme toggle
- [ ] OCR support for scanned PDFs
- [ ] Batch export to ZIP
- [ ] Markdown preview with syntax highlighting
- [ ] Custom CSS styles for PDF-to-MD conversion
- [ ] Progress persistence across app restarts
- [ ] Plugin system for custom converters

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) — PDF text extraction
- [Flask](https://flask.palletsprojects.com/) — Backend web framework
- [PyWebView](https://pywebview.flowrl.com/) — Native desktop window wrapper
- [PyInstaller](https://pyinstaller.org/) — Executable packaging

---

<p align="center">Built with ❤️ for the open-source community</p>
