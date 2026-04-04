"""Compare two PDF files and show differences."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fitz
from PIL import Image, ImageDraw
import cv2
import numpy as np

from . import utils


class PDFComparator:
    """Compare two PDF files page-by-page and detect differences."""

    def __init__(self, threshold: float = 1.0) -> None:
        """Initialize comparator.

        Args:
            threshold: Pixel difference threshold (percentage 0-100).
                Lower threshold = more sensitive to small differences.
        """
        self.threshold = threshold

    def _render_page(self, doc: fitz.Document, page_num: int, dpi: int) -> Image.Image:
        """Render a PDF page to PIL Image."""
        return utils.render_page_to_image(doc, page_num, dpi)

    def _compare_images(
        self,
        img1: Image.Image,
        img2: Image.Image,
        diff_color: Tuple[int, int, int] = (255, 0, 0),
    ) -> Tuple[float, Image.Image]:
        """Compare two images and return difference percentage and visualization."""
        # Resize to match if sizes differ
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        # Convert to numpy arrays
        arr1 = np.array(img1.convert("RGB"))
        arr2 = np.array(img2.convert("RGB"))

        # Calculate absolute difference
        diff = np.abs(arr1 - arr2)
        # Sum differences across all channels
        diff_sum = np.sum(diff, axis=2)
        # Calculate percentage of differing pixels
        differing_pixels = np.sum(diff_sum > 0)
        total_pixels = diff_sum.size
        diff_percent = (differing_pixels / total_pixels) * 100

        # Create visualization
        vis = img1.copy()
        draw = ImageDraw.Draw(vis)

        # Find contours of differences with OpenCV
        diff_mask = (diff_sum > 0).astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            diff_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Draw bounding boxes around differences
        for contour in contours:
            # Filter out very small noise
            if cv2.contourArea(contour) < 10:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            # Draw rectangle with red border
            draw.rectangle([x, y, x + w, y + h], outline=diff_color, width=2)

        return diff_percent, vis

    def compare(
        self,
        pdf1_path: Path | str,
        pdf2_path: Path | str,
        output_diff_dir: Optional[Path | str] = None,
        dpi: int = 150,
        highlight_color: Tuple[int, int, int] = (255, 0, 0),
        overwrite: bool = False,
    ) -> Dict[
        str,
        int | float | bool | None | List[Dict[str, int | float | bool | str | None]],
    ]:
        """Compare two PDF files.

        Comparison is page-by-page. If PDFs have different number of pages,
        it compares the overlapping pages and notes the difference in count.

        Args:
            pdf1_path: First PDF (base/expected)
            pdf2_path: Second PDF (comparison/current)
            output_diff_dir: Directory to save difference visualization images
            dpi: DPI for rendering when comparing
            highlight_color: Color for highlighting differences (RGB)
            overwrite: Whether to overwrite existing output files

        Returns:
            Comparison result with summary and page-by-page details
        """
        valid, error = utils.validate_pdf_file(pdf1_path)
        if not valid:
            raise ValueError(error)
        valid, error = utils.validate_pdf_file(pdf2_path)
        if not valid:
            raise ValueError(error)

        if output_diff_dir:
            output_diff_dir = Path(output_diff_dir)
            output_diff_dir.mkdir(parents=True, exist_ok=True)

        pdf1 = fitz.open(pdf1_path)
        pdf2 = fitz.open(pdf2_path)

        pages1 = len(pdf1)
        pages2 = len(pdf2)
        max_pages = max(pages1, pages2)

        total_diff_pages = 0
        page_results = []

        for page_num in range(max_pages):
            page_result: Dict[str, int | bool | float | None | str] = {
                "page_number": page_num + 1,
                "exists_in_pdf1": page_num < pages1,
                "exists_in_pdf2": page_num < pages2,
                "diff_percent": None,
                "diff_image_path": None,
                "has_differences": False,
            }

            if page_num < pages1 and page_num < pages2:
                # Both have this page - compare
                img1 = self._render_page(pdf1, page_num, dpi)
                img2 = self._render_page(pdf2, page_num, dpi)
                diff_percent, diff_image = self._compare_images(
                    img1, img2, highlight_color
                )

                page_result["diff_percent"] = round(diff_percent, 2)
                has_diff = diff_percent > self.threshold

                if has_diff:
                    total_diff_pages += 1
                    page_result["has_differences"] = True

                    # Save difference image if output directory is provided
                    if output_diff_dir:
                        diff_path = output_diff_dir / f"diff_page_{page_num + 1}.png"
                        if diff_path.exists() and not overwrite:
                            raise ValueError(f"Output file already exists: {diff_path}")
                        diff_image.save(diff_path)
                        page_result["diff_image_path"] = str(diff_path)

            elif page_num >= pages1:
                # Only in second PDF
                total_diff_pages += 1
                page_result["has_differences"] = True
                page_result["note"] = "Extra page in second PDF"
            else:
                # Only in first PDF
                total_diff_pages += 1
                page_result["has_differences"] = True
                page_result["note"] = "Page missing in second PDF"

            page_results.append(page_result)

        pdf1.close()
        pdf2.close()

        return {
            "pdf1_pages": pages1,
            "pdf2_pages": pages2,
            "different_page_count": pages1 != pages2,
            "pages_with_differences": total_diff_pages,
            "total_pages_compared": max_pages,
            "different_percent": (
                round((total_diff_pages / max_pages) * 100, 2) if max_pages > 0 else 0
            ),
            "identical": total_diff_pages == 0,
            "pages": page_results,
        }
