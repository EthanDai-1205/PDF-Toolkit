"""Convert PDF pages to image files."""

from pathlib import Path
from typing import List, Dict, Optional, Any
import fitz
from PIL import Image

from . import utils


class PDFToImageConverter:
    """Convert PDF pages to image files (PNG/JPEG)."""

    def convert(
        self,
        input_file: Path | str,
        output_dir: Path | str,
        page_ranges: Optional[str] = None,
        dpi: int = 300,
        format: str = "png",
        quality: int = 90,
        grayscale: bool = False,
        prefix: str = "",
        overwrite: bool = False,
    ) -> List[Dict[str, int | str]]:
        """Convert PDF pages to images.

        Args:
            input_file: Input PDF file
            output_dir: Output directory for images
            page_ranges: Optional page range string (e.g., "1-5,7")
            dpi: Resolution in DPI (higher = better quality, larger file)
            format: Output format - "png" or "jpeg"
            quality: JPEG quality (0-100), only used for JPEG
            grayscale: Whether to convert to grayscale
            prefix: Prefix for output filenames
            overwrite: Whether to overwrite existing files

        Returns:
            List of result info for each converted page
        """
        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        format = format.lower()
        if format not in ["png", "jpeg", "jpg"]:
            raise ValueError("Format must be 'png' or 'jpeg'/'jpg'")

        input_path = Path(input_file)
        if not prefix:
            prefix = input_path.stem

        doc = fitz.open(input_path)
        total_pages = len(doc)

        if page_ranges:
            pages = utils.parse_page_ranges(page_ranges, total_pages)
        else:
            pages = list(range(total_pages))

        results = []
        zoom = dpi / 72  # 72 is default PDF DPI
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in pages:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)

            if grayscale:
                pix = fitz.Pixmap(pix, 0)  # Convert to grayscale

            # Convert to PIL Image
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # Generate output filename
            page_num_1based = page_num + 1
            if format == "png":
                output_filename = f"{prefix}_page_{page_num_1based}.png"
            else:
                output_filename = f"{prefix}_page_{page_num_1based}.jpg"

            output_path = output_dir / output_filename

            if output_path.exists() and not overwrite:
                doc.close()
                raise ValueError(f"Output file already exists: {output_path}")

            # Save
            save_kwargs = {}
            if format in ["jpeg", "jpg"]:
                save_kwargs["quality"] = quality
                if grayscale:
                    img = img.convert("L")
            elif format == "png" and grayscale:
                img = img.convert("L")

            img.save(output_path, format=format.upper(), **save_kwargs)

            results.append(
                {
                    "output_path": str(output_path),
                    "page_number": page_num_1based,
                    "width": pix.width,
                    "height": pix.height,
                    "dpi": dpi,
                }
            )

        doc.close()
        return results

    def convert_single_page(
        self,
        input_file: Path | str,
        output_path: Path | str,
        page_number: int,
        **kwargs: Any,
    ) -> Dict[str, int | str]:
        """Convert a single page to image.

        Args:
            input_file: Input PDF file
            output_path: Output image file
            page_number: Page number (1-indexed)
            **kwargs: Other conversion options

        Returns:
            Result info
        """
        dpi = kwargs.get("dpi", 300)
        format = kwargs.get("format", "png")
        quality = kwargs.get("quality", 90)
        grayscale = kwargs.get("grayscale", False)
        overwrite = kwargs.get("overwrite", False)

        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        valid, error = utils.validate_output_path(output_path, overwrite)
        if not valid:
            raise ValueError(error)

        output_path = Path(output_path)
        doc = fitz.open(input_file)
        total_pages = len(doc)

        if page_number < 1 or page_number > total_pages:
            doc.close()
            raise ValueError(
                f"Page number {page_number} out of range (1-{total_pages})"
            )

        page_num = page_number - 1
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        page = doc[page_num]
        pix = page.get_pixmap(matrix=matrix)

        if grayscale:
            pix = fitz.Pixmap(pix, 0)

        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        if grayscale:
            img = img.convert("L")

        format = output_path.suffix.lower().lstrip(".")
        if format == "jpg":
            format = "jpeg"

        save_kwargs = {}
        if format == "jpeg":
            save_kwargs["quality"] = quality

        img.save(output_path, format=format.upper(), **save_kwargs)
        doc.close()

        return {
            "output_path": str(output_path),
            "width": pix.width,
            "height": pix.height,
            "dpi": dpi,
        }
