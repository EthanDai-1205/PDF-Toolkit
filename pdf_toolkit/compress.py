"""Compress PDF to reduce file size."""

import subprocess
from pathlib import Path
from typing import Dict, Any
import fitz

from . import utils


class PDFCompressor:
    """Compress PDF files with multiple compression strategies."""

    def __init__(self) -> None:
        self._has_ghostscript = self._check_ghostscript()

    def _check_ghostscript(self) -> bool:
        """Check if Ghostscript is available."""
        try:
            result = subprocess.run(["gs", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def has_ghostscript(self) -> bool:
        """Return whether Ghostscript is available for additional compression."""
        return self._has_ghostscript

    def compress_pymupdf(
        self,
        input_file: Path | str,
        output_path: Path | str,
        image_quality: int = 80,
        dpi_limit: int = 150,
        overwrite: bool = False,
    ) -> Dict[str, int | float | str]:
        """Compress PDF using PyMuPDF built-in methods.

        Args:
            input_file: Input PDF file
            output_path: Output compressed PDF
            image_quality: JPEG quality (0-100), lower = smaller file
            dpi_limit: Maximum DPI for images, downsample if higher
            overwrite: Whether to overwrite existing file

        Returns:
            Compression result with sizes and ratio
        """
        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        valid, error = utils.validate_output_path(output_path, overwrite)
        if not valid:
            raise ValueError(error)

        input_path = Path(input_file)
        output_path = Path(output_path)
        input_size = input_path.stat().st_size

        doc = fitz.open(input_path)

        # Process each page to optimize images
        for page in doc:
            # Get all images on the page
            image_list = page.get_images(full=True)

            for img in image_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                # Only re-compress if image is above quality threshold
                # This reduces image quality to save space
                try:
                    pix = fitz.Pixmap(doc, xref)
                    needs_replacement = False

                    if pix.n > 4:  # CMYK
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                        needs_replacement = True

                    # Calculate current DPI, downsample if needed
                    if pix.width > 0 and page.rect.width > 0:
                        current_dpi = (pix.width * 72) / page.rect.width
                        if current_dpi > dpi_limit:
                            # Need to downsample
                            scale = dpi_limit / current_dpi
                            new_width = max(1, int(pix.width * scale))
                            new_height = max(1, int(pix.height * scale))
                            pix = pix.scaled(new_width, new_height)
                            needs_replacement = True

                    # Only replace if we actually changed it
                    # This avoids unnecessary recompression
                    if needs_replacement:
                        page.replace_image(xref, pix, quality=image_quality)

                    pix = None  # Help with garbage collection
                except Exception:
                    # Skip problematic images
                    continue

        # Save with garbage collection and deflate
        doc.save(
            output_path,
            garbage=4,  # maximum garbage collection
            deflate=True,  # compress streams
            clean=True,  # clean unused objects
            linear=False,
        )
        doc.close()

        output_size = output_path.stat().st_size
        compression_ratio = 100 - (output_size * 100 / input_size)

        return {
            "input_size_bytes": input_size,
            "output_size_bytes": output_size,
            "compression_ratio_percent": round(compression_ratio, 2),
            "method": "pymupdf",
        }

    def compress_ghostscript(
        self,
        input_file: Path | str,
        output_path: Path | str,
        quality: str = "ebook",
        overwrite: bool = False,
    ) -> Dict[str, int | float | str]:
        """Compress PDF using Ghostscript (higher compression).

        Quality options:
        - screen: Low quality, smallest size (72 dpi)
        - ebook: Medium quality (150 dpi) - default
        - printer: High quality (300 dpi)
        - prepress: High quality with color preservation (300 dpi)

        Args:
            input_file: Input PDF file
            output_path: Output compressed PDF
            quality: Ghostscript quality setting
            overwrite: Whether to overwrite existing file

        Returns:
            Compression result with sizes and ratio
        """
        if not self._has_ghostscript:
            raise RuntimeError(
                "Ghostscript not found. Please install Ghostscript first:\n"
                "  - macOS: brew install ghostscript\n"
                "  - Ubuntu/Debian: apt-get install ghostscript\n"
                "  - Windows: download from https://www.ghostscript.com/"
            )

        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        valid, error = utils.validate_output_path(output_path, overwrite)
        if not valid:
            raise ValueError(error)

        input_path = Path(input_file)
        output_path = Path(output_path)
        input_size = input_path.stat().st_size

        # Ghostscript command
        quality_settings = {
            "screen": "/screen",
            "ebook": "/ebook",
            "printer": "/printer",
            "prepress": "/prepress",
        }
        gs_quality = quality_settings.get(quality, "/ebook")

        cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            f"-dPDFSETTINGS={gs_quality}",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            str(input_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Ghostscript compression failed: {result.stderr}")

        output_size = output_path.stat().st_size
        compression_ratio = 100 - (output_size * 100 / input_size)

        return {
            "input_size_bytes": input_size,
            "output_size_bytes": output_size,
            "compression_ratio_percent": round(compression_ratio, 2),
            "method": "ghostscript",
            "quality": quality,
        }

    def compress(
        self,
        input_file: Path | str,
        output_path: Path | str,
        use_ghostscript: bool = True,
        **kwargs: Any,
    ) -> Dict[str, int | float | str]:
        """Compress PDF - tries Ghostscript if available, falls back to PyMuPDF.

        Args:
            input_file: Input PDF file
            output_path: Output compressed PDF
            use_ghostscript: Whether to use Ghostscript if available
            **kwargs: Compression parameters

        Returns:
            Compression result
        """
        if use_ghostscript and self._has_ghostscript:
            quality = kwargs.get("quality", "ebook")
            return self.compress_ghostscript(input_file, output_path, quality, **kwargs)
        else:
            image_quality = kwargs.get("image_quality", 80)
            dpi_limit = kwargs.get("dpi_limit", 150)
            return self.compress_pymupdf(
                input_file, output_path, image_quality, dpi_limit, **kwargs
            )
