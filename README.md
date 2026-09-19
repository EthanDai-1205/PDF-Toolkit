# PDF Toolkit

A comprehensive Python PDF toolkit with all essential PDF processing features:

- **Merge** - Combine multiple PDF files into one
- **Split** - Split PDF into multiple files
- **Extract** - Extract specific pages from PDF
- **Compress** - Reduce PDF file size
- **PDF to Image** - Convert PDF pages to PNG/JPEG images
- **Image to PDF** - Convert image files to PDF
- **Compare** - Compare two PDFs with visual difference highlighting

## Requirements

- Python 3.9+
- (Optional) Ghostscript for better PDF compression - see installation below

## Installation

1. Activate your virtual environment (recommended):
```bash
cd pdf-toolkit
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Installing Ghostscript (optional, for better compression)

**macOS:**
```bash
brew install ghostscript
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ghostscript
```

**Windows:**
Download from https://www.ghostscript.com/ and add to PATH.

## Usage

Run using `python -m pdf_toolkit` or install the CLI:

```bash
python -m pdf_toolkit --help
```

### Commands

#### Merge PDFs

```bash
python -m pdf_toolkit merge file1.pdf file2.pdf -o merged.pdf --overwrite
```

Options:
- `--output, -o` - Output merged PDF (required)
- `--no-bookmarks` - Don't add bookmarks for each input file
- `--overwrite, -f` - Overwrite output if exists

#### Split PDF by page count

Split into individual pages:
```bash
python -m pdf_toolkit split input.pdf -o output_dir/ -n 1 -p myprefix --overwrite
```

Split into chunks of 5 pages each:
```bash
python -m pdf_toolkit split input.pdf -o output_dir/ -n 5 --overwrite
```

Options:
- `--output-dir, -o` - Output directory (required)
- `--by-pages, -n` - Number of pages per file (default: 1)
- `--prefix, -p` - Prefix for output filenames
- `--overwrite, -f` - Overwrite output if exists

#### Extract specific pages

Extract pages 1-3 and page 5 to a new PDF:
```bash
python -m pdf_toolkit extract input.pdf -o extracted.pdf --pages "1-3,5" --overwrite
```

Options:
- `--output, -o` - Output PDF (required)
- `--pages, -p` - Page ranges (required), e.g. `"1-5,7,9-10"`

#### Compress PDF

Uses Ghostscript automatically if available, falls back to PyMuPDF:
```bash
python -m pdf_toolkit compress input.pdf -o compressed.pdf --overwrite
```

Different quality settings (Ghostscript only):
```bash
python -m pdf_toolkit compress input.pdf -o compressed.pdf --quality screen --overwrite
```

Quality options:
- `screen` - Lowest quality, smallest file (72 dpi)
- `ebook` - Medium quality (150 dpi) - default
- `printer` - High quality (300 dpi)
- `prepress` - High quality with color preservation (300 dpi)

Force PyMuPDF even if Ghostscript is available:
```bash
python -m pdf_toolkit compress input.pdf -o compressed.pdf --no-ghostscript --image-quality 60 --dpi-limit 100 --overwrite
```

#### PDF to Image

Convert all pages to PNG:
```bash
python -m pdf_toolkit pdf-to-image input.pdf -o output_dir/ --dpi 300 --format png --overwrite
```

Convert specific pages to JPEG:
```bash
python -m pdf_toolkit pdf-to-image input.pdf -o output_dir/ --pages "1-3,5" --dpi 200 --format jpeg --quality 90 --grayscale --overwrite
```

Options:
- `--output-dir, -o` - Output directory (required)
- `--pages, -p` - Page ranges (default: all)
- `--dpi, -d` - Resolution in DPI (default: 300)
- `--format, -f` - `png` or `jpeg` (default: png)
- `--quality, -q` - JPEG quality 0-100 (default: 90)
- `--grayscale, -g` - Convert to grayscale
- `--prefix` - Prefix for output filenames
- `--overwrite, -f` - Overwrite output if exists

#### Image to PDF

Convert multiple images to single PDF with auto page size:
```bash
python -m pdf_toolkit image-to-pdf img1.jpg img2.png -o output.pdf --overwrite
```

Convert images to A4 PDF:
```bash
python -m pdf_toolkit image-to-pdf *.jpg -o output.pdf --page-size a4 --orientation portrait --margin 36 --overwrite
```

Options:
- `--output, -o` - Output PDF (required)
- `--page-size, -p` - `auto`, `a4`, `a3`, `letter`, `legal` (default: auto)
- `--orientation, -r` - `portrait` or `landscape` for fixed page sizes
- `--quality, -q` - JPEG quality 0-100 (default: 90)
- `--fit, -f` - `contain` (keep aspect, center) or `stretch` (fill page) (default: contain)
- `--margin, -m` - Margin in points (default: 0)
- `--overwrite, -f` - Overwrite output if exists

#### Convert all images in a folder to PDF

```bash
python -m pdf_toolkit image-folder-to-pdf images/ -o output.pdf --page-size a4 --sort-by name --overwrite
```

Options:
- `--sort-by, -s` - `name` or `modified` (default: name)
- (other options same as `image-to-pdf`)

#### Compare PDFs

Compare two PDFs and report differences:
```bash
python -m pdf_toolkit compare original.pdf modified.pdf
```

Save difference visualization images:
```bash
python -m pdf_toolkit compare original.pdf modified.pdf -o diffs/
```

With custom sensitivity (lower threshold = more sensitive):
```bash
python -m pdf_toolkit compare original.pdf modified.pdf -o diffs/ --threshold 0.5
```

Exit code is 0 if identical, 1 if different.

Options:
- `--output-dir, -o` - Directory to save difference visualization images (optional)
- `--dpi, -d` - DPI for rendering (default: 150)
- `--threshold, -t` - Difference threshold in percent (default: 1.0)

## Running Tests

```bash
pytest
```

Check coverage:
```bash
pytest --cov=pdf_toolkit --cov-report=html
# Open htmlcov/index.html in browser
```

Code quality checks:

```bash
black pdf_toolkit tests
flake8 pdf_toolkit tests
mypy pdf_toolkit
```

## Libraries Used

- **PyMuPDF (fitz)** - Core PDF manipulation (fast, C-backed)
- **Pillow** - Image processing
- **OpenCV** - Visual difference detection for comparison
- **Click** - Command-line interface
- **pytest** - Testing

## License

MIT

