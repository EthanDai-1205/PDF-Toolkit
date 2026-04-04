"""Gradio web UI for PDF Toolkit."""

import os
import tempfile
from pathlib import Path
from typing import Tuple

import gradio as gr

from .merge import PDFMerger
from .split import PDFSplitter
from .compress import PDFCompressor
from .pdf_to_image import PDFToImageConverter
from .image_to_pdf import ImageToPDFConverter
from .compare import PDFComparator


def merge_pdfs_ui(
    input_files: list[gr.FileData], add_bookmarks: bool
) -> Tuple[str, Tuple[bytes, str]]:
    """Merge multiple PDFs from UI."""
    if not input_files:
        raise ValueError("Please select at least one PDF file")

    input_paths = [f.name for f in input_files]
    output_path = tempfile.mktemp(suffix=".pdf")

    merger = PDFMerger()
    result = merger.merge(
        input_paths, output_path, add_bookmarks=add_bookmarks, overwrite=True
    )

    with open(output_path, "rb") as f:
        content = f.read()

    filename = "merged.pdf"
    os.unlink(output_path)

    return (
        f"✓ Merged {result['input_files']} files into {result['total_pages']} total pages",
        (content, filename),
    )


def split_pdf_ui(
    input_file: gr.FileData, pages_per_file: int, prefix: str
) -> list[Tuple[bytes, str]]:
    """Split PDF into multiple files."""
    if not input_file:
        raise ValueError("Please select a PDF file")

    output_dir = tempfile.mkdtemp()
    splitter = PDFSplitter()
    results = splitter.split_by_pages(
        input_file.name,
        output_dir,
        pages_per_file=pages_per_file,
        prefix=prefix,
        overwrite=True,
    )

    output_files = []
    for res in results:
        output_path = res["output_path"]
        assert isinstance(output_path, str)
        with open(output_path, "rb") as f:
            content = f.read()
        filename = Path(output_path).name
        output_files.append((content, filename))
        os.unlink(output_path)

    os.rmdir(output_dir)
    return output_files


def extract_pages_ui(input_file: gr.FileData, pages: str) -> Tuple[str, Tuple[bytes, str]]:
    """Extract specific pages from PDF."""
    if not input_file:
        raise ValueError("Please select a PDF file")

    output_path = tempfile.mktemp(suffix=".pdf")
    splitter = PDFSplitter()
    result = splitter.extract_pages(input_file.name, output_path, pages, overwrite=True)

    with open(output_path, "rb") as f:
        content = f.read()

    filename = "extracted.pdf"
    os.unlink(output_path)

    return (
        f"✓ Extracted {result['pages_extracted']} pages",
        (content, filename),
    )


def compress_pdf_ui(
    input_file: gr.FileData,
    use_ghostscript: bool,
    quality: int,
    image_quality: int,
    dpi_limit: int,
) -> Tuple[str, Tuple[bytes, str]]:
    """Compress PDF."""
    if not input_file:
        raise ValueError("Please select a PDF file")

    output_path = tempfile.mktemp(suffix=".pdf")
    compressor = PDFCompressor()

    result = compressor.compress(
        input_file.name,
        output_path,
        use_ghostscript=use_ghostscript,
        quality=(
            "ebook"
            if quality == 75
            else "screen" if quality == 50 else "printer" if quality == 100 else "ebook"
        ),
        image_quality=image_quality,
        dpi_limit=dpi_limit,
        overwrite=True,
    )

    input_kb = int(result["input_size_bytes"]) / 1024
    output_kb = int(result["output_size_bytes"]) / 1024

    with open(output_path, "rb") as f:
        content = f.read()

    filename = f"compressed_{result['method']}.pdf"
    os.unlink(output_path)

    return (
        f"✓ Compressed with {result['method']}\nOriginal: {input_kb:.1f} KB\nCompressed: {output_kb:.1f} KB\nReduction: {result['compression_ratio_percent']:.1f}%",
        (content, filename),
    )


def pdf_to_image_ui(
    input_file: gr.FileData, dpi: int, format: str, grayscale: bool
) -> list[Tuple[bytes, str]]:
    """Convert PDF pages to images."""
    if not input_file:
        raise ValueError("Please select a PDF file")

    output_dir = tempfile.mkdtemp()
    converter = PDFToImageConverter()
    results = converter.convert(
        input_file.name,
        output_dir,
        dpi=dpi,
        format=format,
        grayscale=grayscale,
        overwrite=True,
    )

    output_images = []
    for res in results:
        output_path = res["output_path"]
        assert isinstance(output_path, str)
        with open(output_path, "rb") as f:
            content = f.read()
        filename = Path(output_path).name
        output_images.append((content, filename))
        os.unlink(output_path)

    os.rmdir(output_dir)
    return output_images


def image_to_pdf_ui(
    input_files: list[gr.FileData],
    page_size: str,
    orientation: str,
    quality: int,
    fit: str,
    margin: int,
) -> Tuple[str, Tuple[bytes, str]]:
    """Convert multiple images to PDF."""
    if not input_files:
        raise ValueError("Please select at least one image")

    input_paths = [f.name for f in input_files]
    output_path = tempfile.mktemp(suffix=".pdf")

    converter = ImageToPDFConverter()
    result = converter.convert(
        input_paths,
        output_path,
        page_size=page_size if page_size != "auto" else "auto",
        orientation=orientation,
        quality=quality,
        fit=fit,
        margin=margin,
        overwrite=True,
    )

    with open(output_path, "rb") as f:
        content = f.read()

    filename = "images.pdf"
    os.unlink(output_path)

    return (
        f"✓ Converted {result['images_processed']} images into {result['pages_in_output']} pages",
        (content, filename),
    )


def compare_pdfs_ui(
    pdf1: gr.FileData, pdf2: gr.FileData, threshold: float, dpi: int
) -> Tuple[str, list[Tuple[bytes, str]]]:
    """Compare two PDFs and return difference images."""
    if not pdf1 or not pdf2:
        raise ValueError("Please select both PDF files")

    output_dir = tempfile.mkdtemp()
    comparator = PDFComparator(threshold=threshold)
    result = comparator.compare(
        pdf1.name, pdf2.name, output_diff_dir=output_dir, dpi=dpi, overwrite=True
    )

    output_images = []

    pages_with_differences = result["pages_with_differences"]
    assert isinstance(pages_with_differences, int)
    pages = result["pages"]
    assert isinstance(pages, list)

    if pages_with_differences > 0 and output_dir:
        for page in pages:
            diff_path = page.get("diff_image_path")
            if diff_path:
                assert isinstance(diff_path, str)
                with open(diff_path, "rb") as f:
                    content = f.read()
                filename = Path(diff_path).name
                output_images.append((content, filename))
                os.unlink(diff_path)

    os.rmdir(output_dir)

    summary = (
        f"Comparison Result:\n"
        f"PDF 1: {result['pdf1_pages']} pages\n"
        f"PDF 2: {result['pdf2_pages']} pages\n"
        f"Pages with differences: {result['pages_with_differences']}/{result['total_pages_compared']}\n"
        f"Difference percentage: {result['different_percent']}%\n"
        f"Status: {'✅ PDFs are identical' if result['identical'] else '⚠️ PDFs have differences'}"
    )

    return summary, output_images


def create_app() -> gr.Blocks:
    """Create the Gradio app."""
    with gr.Blocks(title="PDF Toolkit") as app:
        gr.Markdown(
            "# 📄 PDF Toolkit\n"
            "A comprehensive PDF processing toolkit with all core features."
        )

        with gr.Tabs():
            # Merge Tab
            with gr.Tab("📎 Merge PDFs"):
                gr.Markdown("Merge multiple PDF files into one.")
                merge_inputs = [
                    gr.File(
                        file_count="multiple",
                        label="Input PDF Files",
                        file_types=[".pdf"],
                    ),
                    gr.Checkbox(value=True, label="Add bookmarks for each input file"),
                ]
                merge_output = [
                    gr.Textbox(label="Result"),
                    gr.File(label="Merged PDF"),
                ]
                gr.Button("Merge PDFs").click(
                    merge_pdfs_ui, inputs=merge_inputs, outputs=merge_output
                )

            # Split Tab
            with gr.Tab("✂️ Split PDF"):
                gr.Markdown("Split a PDF into multiple files by page count.")
                split_inputs = [
                    gr.File(
                        file_count="single", label="Input PDF", file_types=[".pdf"]
                    ),
                    gr.Number(value=1, label="Pages per output file", minimum=1),
                    gr.Textbox(value="", label="Filename prefix"),
                ]
                split_output = gr.File(file_count="multiple", label="Output Files")
                gr.Button("Split PDF").click(
                    split_pdf_ui, inputs=split_inputs, outputs=split_output
                )

            # Extract Tab
            with gr.Tab("📑 Extract Pages"):
                gr.Markdown("Extract specific pages from a PDF to a new file.")
                extract_inputs = [
                    gr.File(
                        file_count="single", label="Input PDF", file_types=[".pdf"]
                    ),
                    gr.Textbox(
                        label="Page ranges (e.g., 1-5,7,9-10)", placeholder="1-5,8"
                    ),
                ]
                extract_output = [
                    gr.Textbox(label="Result"),
                    gr.File(label="Extracted PDF"),
                ]
                gr.Button("Extract Pages").click(
                    extract_pages_ui, inputs=extract_inputs, outputs=extract_output
                )

            # Compress Tab
            with gr.Tab("🗜️ Compress PDF"):
                gr.Markdown("Compress PDF to reduce file size.")
                compress_inputs = [
                    gr.File(
                        file_count="single", label="Input PDF", file_types=[".pdf"]
                    ),
                    gr.Checkbox(
                        value=True,
                        label="Use Ghostscript if available (better compression)",
                    ),
                    gr.Slider(
                        minimum=50,
                        maximum=100,
                        value=75,
                        step=25,
                        label="Quality level (Ghostscript)",
                    ),
                    gr.Slider(
                        minimum=30,
                        maximum=100,
                        value=80,
                        label="Image quality (PyMuPDF)",
                    ),
                    gr.Slider(
                        minimum=72,
                        maximum=300,
                        value=150,
                        step=10,
                        label="Max DPI (PyMuPDF)",
                    ),
                ]
                compress_output = [
                    gr.Textbox(label="Result"),
                    gr.File(label="Compressed PDF"),
                ]
                gr.Button("Compress PDF").click(
                    compress_pdf_ui, inputs=compress_inputs, outputs=compress_output
                )

            # PDF to Image Tab
            with gr.Tab("🖼️ PDF to Image"):
                gr.Markdown("Convert PDF pages to image files.")
                pti_inputs = [
                    gr.File(
                        file_count="single", label="Input PDF", file_types=[".pdf"]
                    ),
                    gr.Slider(
                        minimum=72,
                        maximum=600,
                        value=300,
                        step=25,
                        label="DPI (Resolution)",
                    ),
                    gr.Radio(
                        choices=["png", "jpeg"], value="png", label="Output format"
                    ),
                    gr.Checkbox(value=False, label="Convert to grayscale"),
                ]
                pti_output = gr.File(file_count="multiple", label="Output Images")
                gr.Button("Convert").click(
                    pdf_to_image_ui, inputs=pti_inputs, outputs=pti_output
                )

            # Image to PDF Tab
            with gr.Tab("🖼️ Image to PDF"):
                gr.Markdown("Convert multiple image files to a single PDF.")
                itp_inputs = [
                    gr.File(
                        file_count="multiple",
                        label="Input Images",
                        file_types=[".png", ".jpg", ".jpeg", ".bmp"],
                    ),
                    gr.Radio(
                        choices=["auto", "a4", "a3", "letter", "legal"],
                        value="auto",
                        label="Page size",
                    ),
                    gr.Radio(
                        choices=["portrait", "landscape"],
                        value="portrait",
                        label="Orientation (for fixed sizes)",
                    ),
                    gr.Slider(minimum=30, maximum=100, value=90, label="JPEG quality"),
                    gr.Radio(
                        choices=["contain", "stretch"],
                        value="contain",
                        label="Fit mode",
                    ),
                    gr.Number(value=0, label="Margin (points)", minimum=0),
                ]
                itp_output = [
                    gr.Textbox(label="Result"),
                    gr.File(label="Output PDF"),
                ]
                gr.Button("Convert").click(
                    image_to_pdf_ui, inputs=itp_inputs, outputs=itp_output
                )

            # Compare Tab
            with gr.Tab("🔍 Compare PDFs"):
                gr.Markdown("Compare two PDF files and visualize differences.")
                compare_inputs = [
                    gr.File(
                        file_count="single", label="PDF 1 (Base)", file_types=[".pdf"]
                    ),
                    gr.File(
                        file_count="single",
                        label="PDF 2 (Compare)",
                        file_types=[".pdf"],
                    ),
                    gr.Slider(
                        minimum=0.0,
                        maximum=10.0,
                        value=1.0,
                        step=0.5,
                        label="Difference threshold (%)",
                    ),
                    gr.Slider(
                        minimum=72, maximum=300, value=150, step=25, label="Render DPI"
                    ),
                ]
                compare_output = [
                    gr.Textbox(label="Summary"),
                    gr.File(file_count="multiple", label="Difference images"),
                ]
                gr.Button("Compare").click(
                    compare_pdfs_ui, inputs=compare_inputs, outputs=compare_output
                )

        gr.Markdown(
            "---\n" "Built with [PDF Toolkit](https://github.com/), using Gradio."
        )

    return app


def main() -> None:
    """Run the Gradio app."""
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        show_error=True,
    )


if __name__ == "__main__":
    main()
