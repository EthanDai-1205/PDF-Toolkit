"""Command-line interface for PDF Toolkit."""

import click
import sys
from typing import Sequence, Optional
from typing import Callable, TypeVar, Any

from . import __version__
from .merge import PDFMerger
from .split import PDFSplitter
from .compress import PDFCompressor
from .pdf_to_image import PDFToImageConverter
from .image_to_pdf import ImageToPDFConverter
from .compare import PDFComparator

# Shared common options
overwrite_option = click.option(
    "--overwrite", "-f", is_flag=True, help="Overwrite output file if it exists"
)

T = TypeVar("T")


def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle exceptions uniformly for all CLI commands."""

    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)
        except RuntimeError as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)

    return wrapper


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """PDF Toolkit - A comprehensive PDF processing toolkit.

    Provides merging, splitting, compression, conversion, and comparison of PDFs.
    """
    pass


@cli.command(name="merge")
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output merged PDF file"
)
@click.option(
    "--no-bookmarks", is_flag=True, help="Do not add bookmarks for each input file"
)
@overwrite_option
@handle_errors
def merge_command(
    input_files: Sequence[str], output: str, no_bookmarks: bool, overwrite: bool
) -> None:
    """Merge multiple PDF files into one.

    INPUT_FILES: One or more input PDF files
    """
    merger = PDFMerger()
    result = merger.merge(
        input_files, output, add_bookmarks=not no_bookmarks, overwrite=overwrite
    )
    click.echo(f"✓ Merged {result['input_files']} files into {output}")
    click.echo(f"  Total pages: {result['total_pages']}")


@cli.command(name="split")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", required=True, type=click.Path(), help="Output directory"
)
@click.option(
    "--by-pages",
    "-n",
    type=int,
    default=1,
    help="Number of pages per output file (default: 1)",
)
@click.option("--prefix", "-p", default="", help="Prefix for output filenames")
@overwrite_option
@handle_errors
def split_command(
    input_file: str, output_dir: str, by_pages: int, prefix: str, overwrite: bool
) -> None:
    """Split a PDF into multiple files by page count."""
    splitter = PDFSplitter()
    results = splitter.split_by_pages(
        input_file,
        output_dir,
        pages_per_file=by_pages,
        prefix=prefix,
        overwrite=overwrite,
    )
    click.echo(f"✓ Split into {len(results)} files")
    for res in results:
        click.echo(
            f"  {res['output_path']}: pages {res['start_page']}-{res['end_page']}"
        )


@cli.command(name="extract")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output PDF file"
)
@click.option("--pages", "-p", required=True, help="Page ranges (e.g., '1-5,7,9-10')")
@overwrite_option
@handle_errors
def extract_command(input_file: str, output: str, pages: str, overwrite: bool) -> None:
    """Extract specific pages from a PDF to a new file."""
    splitter = PDFSplitter()
    result = splitter.extract_pages(input_file, output, pages, overwrite=overwrite)
    click.echo(f"✓ Extracted {result['pages_extracted']} pages to {output}")


@cli.command(name="compress")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output compressed PDF"
)
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["screen", "ebook", "printer", "prepress"]),
    default="ebook",
    help="Quality setting (Ghostscript only)",
)
@click.option(
    "--image-quality", type=int, default=80, help="JPEG quality for PyMuPDF (0-100)"
)
@click.option(
    "--dpi-limit", type=int, default=150, help="Maximum DPI for images (PyMuPDF only)"
)
@click.option(
    "--no-ghostscript",
    is_flag=True,
    help="Force use of PyMuPDF even if Ghostscript is available",
)
@overwrite_option
@handle_errors
def compress_command(
    input_file: str,
    output: str,
    quality: str,
    image_quality: int,
    dpi_limit: int,
    no_ghostscript: bool,
    overwrite: bool,
) -> None:
    """Compress PDF to reduce file size.

    Uses Ghostscript if available for better compression, falls back to PyMuPDF.
    """
    compressor = PDFCompressor()
    result = compressor.compress(
        input_file,
        output,
        use_ghostscript=not no_ghostscript,
        quality=quality,
        image_quality=image_quality,
        dpi_limit=dpi_limit,
        overwrite=overwrite,
    )
    input_size_bytes = result["input_size_bytes"]
    output_size_bytes = result["output_size_bytes"]
    input_kb = float(input_size_bytes) / 1024
    output_kb = float(output_size_bytes) / 1024
    click.echo(f"✓ Compressed with {result['method']}:")
    click.echo(f"  Original: {input_kb:.1f} KB")
    click.echo(f"  Compressed: {output_kb:.1f} KB")
    click.echo(f"  Reduction: {result['compression_ratio_percent']:.1f}%")


@cli.command(name="pdf-to-image")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(),
    help="Output directory for images",
)
@click.option("--pages", "-p", help="Page ranges (e.g., '1-5,7') - default: all pages")
@click.option(
    "--dpi", "-d", type=int, default=300, help="Resolution in DPI (default: 300)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["png", "jpeg"]),
    default="png",
    help="Output format",
)
@click.option(
    "--quality", "-q", type=int, default=90, help="JPEG quality (0-100, default: 90)"
)
@click.option("--grayscale", "-g", is_flag=True, help="Convert to grayscale")
@click.option("--prefix", default="", help="Prefix for output filenames")
@overwrite_option
@handle_errors
def pdf_to_image_command(
    input_file: str,
    output_dir: str,
    pages: Optional[str],
    dpi: int,
    format: str,
    quality: int,
    grayscale: bool,
    prefix: str,
    overwrite: bool,
) -> None:
    """Convert PDF pages to image files."""
    converter = PDFToImageConverter()
    results = converter.convert(
        input_file,
        output_dir,
        page_ranges=pages,
        dpi=dpi,
        format=format,
        quality=quality,
        grayscale=grayscale,
        prefix=prefix,
        overwrite=overwrite,
    )
    click.echo(f"✓ Converted {len(results)} pages to {format}")
    for res in results:
        click.echo(
            f"  {res['output_path']} ({res['width']}x{res['height']}, "
            f"{res['dpi']} DPI)"
        )


@cli.command(name="image-to-pdf")
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output PDF file"
)
@click.option(
    "--page-size",
    "-p",
    default="auto",
    type=click.Choice(["auto", "a4", "a3", "letter", "legal"]),
    help="Page size (auto fits to image, default: auto)",
)
@click.option(
    "--orientation",
    "-r",
    default="portrait",
    type=click.Choice(["portrait", "landscape"]),
    help="Page orientation for fixed page sizes",
)
@click.option(
    "--quality", "-q", type=int, default=90, help="JPEG quality (0-100, default: 90)"
)
@click.option(
    "--fit",
    "-f",
    type=click.Choice(["contain", "stretch"]),
    default="contain",
    help="How to fit image on page (default: contain)",
)
@click.option(
    "--margin", "-m", type=int, default=0, help="Margin in points (default: 0)"
)
@overwrite_option
@handle_errors
def image_to_pdf_command(
    input_files: Sequence[str],
    output: str,
    page_size: str,
    orientation: str,
    quality: int,
    fit: str,
    margin: int,
    overwrite: bool,
) -> None:
    """Convert image files to a single PDF."""
    converter = ImageToPDFConverter()
    result = converter.convert(
        input_files,
        output,
        page_size=page_size,
        orientation=orientation,
        quality=quality,
        fit=fit,
        margin=margin,
        overwrite=overwrite,
    )
    click.echo(f"✓ Converted {result['images_processed']} images to {output}")
    click.echo(f"  Total pages: {result['pages_in_output']}")


@cli.command(name="image-folder-to-pdf")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output PDF file"
)
@click.option(
    "--sort-by",
    "-s",
    type=click.Choice(["name", "modified"]),
    default="name",
    help="How to sort images (default: name)",
)
@click.option(
    "--page-size",
    "-p",
    default="auto",
    type=click.Choice(["auto", "a4", "a3", "letter", "legal"]),
    help="Page size (auto fits to image, default: auto)",
)
@click.option(
    "--orientation",
    "-r",
    default="portrait",
    type=click.Choice(["portrait", "landscape"]),
    help="Page orientation for fixed page sizes",
)
@click.option(
    "--quality", "-q", type=int, default=90, help="JPEG quality (0-100, default: 90)"
)
@click.option(
    "--fit",
    "-f",
    type=click.Choice(["contain", "stretch"]),
    default="contain",
    help="How to fit image on page (default: contain)",
)
@click.option(
    "--margin", "-m", type=int, default=0, help="Margin in points (default: 0)"
)
@overwrite_option
@handle_errors
def image_folder_to_pdf_command(
    input_dir: str,
    output: str,
    sort_by: str,
    page_size: str,
    orientation: str,
    quality: int,
    fit: str,
    margin: int,
    overwrite: bool,
) -> None:
    """Convert all images in a folder to a single PDF."""
    converter = ImageToPDFConverter()
    result = converter.convert_folder(
        input_dir,
        output,
        sort_by=sort_by,
        page_size=page_size,
        orientation=orientation,
        quality=quality,
        fit=fit,
        margin=margin,
        overwrite=overwrite,
    )
    click.echo(
        f"✓ Converted {result['images_processed']} images from "
        f"{input_dir} to {output}"
    )
    click.echo(f"  Total pages: {result['pages_in_output']}")


@cli.command(name="compare")
@click.argument("pdf1", type=click.Path(exists=True))
@click.argument("pdf2", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    required=False,
    type=click.Path(),
    help="Output directory for difference visualization images",
)
@click.option(
    "--dpi", "-d", type=int, default=150, help="DPI for rendering (default: 150)"
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=1.0,
    help="Difference threshold in percent (default: 1.0%)",
)
@overwrite_option
@handle_errors
def compare_command(
    pdf1: str,
    pdf2: str,
    output_dir: Optional[str],
    dpi: int,
    threshold: float,
    overwrite: bool,
) -> None:
    """Compare two PDF files and detect differences.

    If --output-dir is provided, difference visualization images with
    highlighted differences will be saved.
    """
    comparator = PDFComparator(threshold=threshold)
    result = comparator.compare(
        pdf1, pdf2, output_diff_dir=output_dir, dpi=dpi, overwrite=overwrite
    )

    click.echo("Comparison result:")
    click.echo(f"  PDF 1: {pdf1} ({result['pdf1_pages']} pages)")
    click.echo(f"  PDF 2: {pdf2} ({result['pdf2_pages']} pages)")

    if result["different_page_count"]:
        click.echo("  ⚠ Different number of pages")

    click.echo(
        f"  Pages with differences: "
        f"{result['pages_with_differences']}/{result['total_pages_compared']}"
    )
    click.echo(f"  Difference percentage: {result['different_percent']}%")

    if result["identical"]:
        click.echo("\n✓ PDFs are identical")
    else:
        click.echo("\n⚠ PDFs have differences")
        if output_dir:
            click.echo(f"  Difference images saved to: {output_dir}")
        # Print page details
        pages = result["pages"]
        assert isinstance(pages, list)
        for page in pages:
            if page["has_differences"]:
                if "note" in page:
                    click.echo(f"  Page {page['page_number']}: {page['note']}")
                else:
                    click.echo(
                        f"  Page {page['page_number']}: "
                        f"{page['diff_percent']}% different"
                    )

    if not result["identical"]:
        exit(1)


if __name__ == "__main__":
    cli()
