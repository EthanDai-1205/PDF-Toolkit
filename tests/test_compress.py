"""Tests for compress module."""

import pytest
from pathlib import Path
import fitz
from pdf_toolkit.compress import PDFCompressor


def create_test_pdf_with_image(path: Path):
    """Create a test PDF with an image for compression testing."""
    from PIL import Image
    import io

    # Create a large test image
    img = Image.new("RGB", (1000, 1000), color="white")
    # Draw something on it
    for x in range(0, 1000, 100):
        for y in range(0, 1000, 100):
            if (x + y) % 200 == 0:
                for dx in range(50):
                    for dy in range(50):
                        img.putpixel((x + dx, y + dy), (255, 0, 0))

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", quality=100)
    img_bytes.seek(0)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=img_bytes.getvalue())
    doc.save(path)
    doc.close()


def test_compress_pymupdf(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "compressed.pdf"
    create_test_pdf_with_image(input_pdf)

    compressor = PDFCompressor()
    result = compressor.compress_pymupdf(
        input_pdf, output_pdf, image_quality=50, dpi_limit=100, overwrite=True
    )

    assert "input_size_bytes" in result
    assert "output_size_bytes" in result
    assert "compression_ratio_percent" in result
    assert output_pdf.exists()
    assert result["method"] == "pymupdf"

    # Should have some compression
    assert result["output_size_bytes"] < result["input_size_bytes"]


def test_compress_output_exists_no_overwrite(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    create_test_pdf_with_image(input_pdf)
    create_test_pdf_with_image(output_pdf)

    compressor = PDFCompressor()
    with pytest.raises(ValueError, match="already exists"):
        compressor.compress_pymupdf(input_pdf, output_pdf, overwrite=False)


def test_has_ghostscript():
    compressor = PDFCompressor()
    # Just check it doesn't crash
    result = compressor.has_ghostscript()
    assert isinstance(result, bool)
