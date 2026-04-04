"""Tests for image_to_pdf module."""

import pytest
from pathlib import Path
from PIL import Image
import fitz
from pdf_toolkit.image_to_pdf import ImageToPDFConverter


def create_test_image(path: Path, size: tuple = (800, 600)):
    """Create a test image."""
    img = Image.new("RGB", size, color="white")
    # Draw some content
    for x in range(0, size[0], 100):
        for y in range(0, size[1], 100):
            if (x + y) % 200 == 0:
                for dx in range(50):
                    for dy in range(50):
                        if 0 <= x + dx < size[0] and 0 <= y + dy < size[1]:
                            img.putpixel((x + dx, y + dy), (255, 0, 0))
    img.save(path, format="JPEG", quality=90)


def test_convert_multiple_images(tmp_path):
    # Create two test images
    img1 = tmp_path / "test1.jpg"
    img2 = tmp_path / "test2.jpg"
    create_test_image(img1, (800, 600))
    create_test_image(img2, (1024, 768))

    output = tmp_path / "output.pdf"

    converter = ImageToPDFConverter()
    result = converter.convert([img1, img2], output, page_size="auto", overwrite=True)

    assert result["images_processed"] == 2
    assert result["pages_in_output"] == 2
    assert output.exists()

    # Verify PDF
    doc = fitz.open(output)
    assert len(doc) == 2
    doc.close()


def test_convert_fixed_page_size(tmp_path):
    img = tmp_path / "test.jpg"
    create_test_image(img, (800, 600))

    output = tmp_path / "output.pdf"

    converter = ImageToPDFConverter()
    _ = converter.convert(
        [img],
        output,
        page_size="a4",
        orientation="portrait",
        margin=36,  # 0.5 inch
        fit="contain",
        overwrite=True,
    )

    assert output.exists()
    doc = fitz.open(output)
    page = doc[0]
    # A4 is 595 x 842
    assert abs(page.rect.width - 595) < 1
    assert abs(page.rect.height - 842) < 1
    doc.close()


def test_convert_folder(tmp_path):
    # Create images in a folder
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    for i in range(3):
        img_path = image_dir / f"image_{i+1}.jpg"
        create_test_image(img_path)

    output = tmp_path / "output.pdf"

    converter = ImageToPDFConverter()
    result = converter.convert_folder(
        image_dir, output, sort_by="name", page_size="a4", overwrite=True
    )

    assert result["images_processed"] == 3
    assert output.exists()
    doc = fitz.open(output)
    assert len(doc) == 3
    doc.close()


def test_invalid_page_size(tmp_path):
    img = tmp_path / "test.jpg"
    create_test_image(img)
    output = tmp_path / "output.pdf"

    converter = ImageToPDFConverter()
    with pytest.raises(ValueError, match="Unknown page size"):
        converter.convert([img], output, page_size="invalid", overwrite=True)


def test_invalid_fit(tmp_path):
    img = tmp_path / "test.jpg"
    create_test_image(img)
    output = tmp_path / "output.pdf"

    converter = ImageToPDFConverter()
    with pytest.raises(ValueError, match="Unknown fit mode"):
        converter.convert([img], output, fit="invalid", overwrite=True)
