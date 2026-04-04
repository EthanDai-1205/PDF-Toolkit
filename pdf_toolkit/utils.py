"""Shared utilities for PDF Toolkit."""

from pathlib import Path
from typing import List, Tuple
import fitz
from PIL import Image

# Valid image extensions
VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
VALID_PDF_EXTENSIONS = {".pdf"}


def validate_pdf_file(file_path: str | Path) -> Tuple[bool, str]:
    """Validate that a file exists and has .pdf extension.

    Args:
        file_path: Path to the PDF file

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    if not path.exists():
        return False, f"File not found: {file_path}"
    if path.suffix.lower() != ".pdf":
        return False, f"Not a PDF file: {file_path}"
    return True, ""


def validate_image_file(file_path: str | Path) -> Tuple[bool, str]:
    """Validate that a file exists and is a supported image format.

    Args:
        file_path: Path to the image file

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    if not path.exists():
        return False, f"File not found: {file_path}"
    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    if path.suffix.lower() not in valid_extensions:
        return (
            False,
            f"Not a supported image file: {file_path}. Supported: {valid_extensions}",
        )
    return True, ""


def validate_output_path(
    output_path: str | Path, overwrite: bool = False
) -> Tuple[bool, str]:
    """Validate output path.

    Args:
        output_path: Path for the output file
        overwrite: Whether to allow overwriting existing file

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(output_path)
    if path.exists() and not overwrite:
        return (
            False,
            f"Output file already exists: {output_path}. "
            f"Use --overwrite to replace it.",
        )
    # Create parent directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    return True, ""


def get_output_directory(output_path: str | Path) -> Path:
    """Ensure output directory exists and return it.

    Args:
        output_path: Output path

    Returns:
        Path object for the output directory
    """
    path = Path(output_path)
    if path.suffix:
        # It's a file, get parent
        directory = path.parent
    else:
        directory = path
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def list_pdf_files(input_dir: str | Path) -> List[Path]:
    """List all PDF files in a directory, sorted by name.

    Args:
        input_dir: Directory to search

    Returns:
        List of Path objects for PDF files
    """
    path = Path(input_dir)
    return sorted([p for p in path.glob("*.pdf") if p.is_file()])


def list_image_files(input_dir: str | Path, sort_by: str = "name") -> List[Path]:
    """List all image files in a directory, sorted.

    Args:
        input_dir: Directory to search
        sort_by: Sort method - "name" or "modified"

    Returns:
        List of Path objects for image files
    """
    path = Path(input_dir)
    image_files: List[Path] = []

    # Check for all case variations of extensions
    for ext in VALID_IMAGE_EXTENSIONS:
        image_files.extend(path.glob(f"*{ext}"))
        image_files.extend(path.glob(f"*{ext.upper()}"))

    # Remove duplicates
    image_files = list(set(image_files))

    # Sort
    if sort_by == "name":
        image_files.sort(key=lambda p: p.name.lower())
    elif sort_by == "modified":
        image_files.sort(key=lambda p: p.stat().st_mtime)

    return image_files


def render_page_to_image(doc: fitz.Document, page_num: int, dpi: int) -> Image.Image:
    """Render a PDF page to a PIL Image.

    Args:
        doc: Open PDF document
        page_num: 0-indexed page number
        dpi: Resolution in DPI

    Returns:
        PIL Image of the rendered page
    """
    zoom = dpi / 72  # 72 is default PDF DPI
    matrix = fitz.Matrix(zoom, zoom)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=matrix)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def parse_page_ranges(ranges_str: str, total_pages: int) -> List[int]:
    """Parse page range string into list of page numbers (0-indexed).

    Supports formats:
    - "1-5": pages 1 to 5 (inclusive)
    - "1,3,5": pages 1, 3, 5
    - "1-5,7-10": multiple ranges
    - "-5": first 5 pages
    - "3-": from page 3 to end

    Note: Page numbers are 1-indexed in input, converted to 0-indexed output.

    Args:
        ranges_str: String representation of page ranges
        total_pages: Total number of pages in the PDF

    Returns:
        List of 0-indexed page numbers
    """
    pages = set()
    parts = ranges_str.replace(" ", "").split(",")

    for part in parts:
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            if start_str == "":
                start = 1
            else:
                start = int(start_str)
            if end_str == "":
                end = total_pages
            else:
                end = int(end_str)
            # Clamp to valid range
            start = max(1, start)
            end = min(total_pages, end)
            for page in range(start, end + 1):
                pages.add(page - 1)  # convert to 0-indexed
        else:
            page = int(part)
            if 1 <= page <= total_pages:
                pages.add(page - 1)

    return sorted(pages)
