"""Convert image files to PDF."""

from pathlib import Path
from typing import Sequence, Any
import fitz
from PIL import Image

from . import utils

# Standard page sizes in points (1 point = 1/72 inch)
PAGE_SIZES = {
    "a4": (595, 842),
    "a3": (842, 1190),
    "letter": (612, 792),
    "legal": (612, 1008),
}


class ImageToPDFConverter:
    """Convert image files to a PDF document."""

    def convert(
        self,
        input_images: Sequence[Path | str],
        output_path: Path | str,
        page_size: str = "auto",
        orientation: str = "portrait",
        quality: int = 90,
        fit: str = "contain",
        margin: int = 0,
        overwrite: bool = False,
    ) -> dict[str, int | str]:
        """Convert multiple images to a single PDF.

        Args:
            input_images: List of input image files
            output_path: Output PDF file
            page_size: Page size - "auto" (fit to image), "a4", "a3", "letter", "legal"
            orientation: "portrait" or "landscape" (used when page_size is not auto)
            quality: JPEG quality for images (0-100)
            fit: How to fit image on page - "contain" (keep aspect, add margins)
               or "stretch" (fill page)
            margin: Margin in points (0 for no margin)
            overwrite: Whether to overwrite existing output file

        Returns:
            Result info
        """
        # Validate inputs
        for input_image in input_images:
            valid, error = utils.validate_image_file(input_image)
            if not valid:
                raise ValueError(error)

        valid, error = utils.validate_output_path(output_path, overwrite)
        if not valid:
            raise ValueError(error)

        output_path = Path(output_path)
        doc = fitz.open()
        quality_val = max(0, min(100, quality))

        for image_path in input_images:
            image_path = Path(image_path)
            img: Image.Image = Image.open(image_path)

            # Convert to RGB if needed
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Get image dimensions in pixels
            img_width, img_height = img.size

            # Determine page dimensions in points
            if page_size == "auto":
                # Calculate page size based on image aspect ratio at 72 DPI
                page_width = img_width
                page_height = img_height
            else:
                # Get standard size
                if page_size.lower() not in PAGE_SIZES:
                    raise ValueError(
                        f"Unknown page size: {page_size}. "
                        f"Available: {list(PAGE_SIZES.keys())}"
                    )

                page_width, page_height = PAGE_SIZES[page_size.lower()]
                if orientation == "landscape":
                    page_width, page_height = page_height, page_width

            # Create page
            page = doc.new_page(width=page_width, height=page_height)

            # Calculate where to place the image
            available_width = page_width - 2 * margin
            available_height = page_height - 2 * margin

            if fit == "contain":
                # Keep aspect ratio, fit within available space
                img_aspect = img_width / img_height
                available_aspect = available_width / available_height
                final_width: float
                final_height: float

                if img_aspect > available_aspect:
                    # Image is wider - width is limiting factor
                    final_width = float(available_width)
                    final_height = final_width / img_aspect
                else:
                    # Image is taller - height is limiting factor
                    final_height = float(available_height)
                    final_width = final_height * img_aspect

            elif fit == "stretch":
                # Fill entire available space
                final_width = float(available_width)
                final_height = float(available_height)
            else:
                raise ValueError(f"Unknown fit mode: {fit}. Use 'contain' or 'stretch'")

            # Calculate position (center)
            x0 = margin + (available_width - final_width) / 2
            y0 = margin + (available_height - final_height) / 2
            rect = fitz.Rect(x0, y0, x0 + final_width, y0 + final_height)

            # Save image to temporary memory and insert into PDF
            # We need to save with the requested quality
            import io

            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=quality_val)
            img_buffer.seek(0)

            page.insert_image(rect, stream=img_buffer)

        # Save PDF
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

        return {
            "images_processed": len(input_images),
            "pages_in_output": len(input_images),
            "output_path": str(output_path),
        }

    def convert_folder(
        self,
        input_dir: Path | str,
        output_path: Path | str,
        sort_by: str = "name",
        **kwargs: Any,
    ) -> dict[str, int | str]:
        """Convert all images in a folder to a single PDF.

        Args:
            input_dir: Input directory containing images
            output_path: Output PDF file
            sort_by: How to sort images - "name" or "modified"
            **kwargs: Other conversion options

        Returns:
            Result info
        """
        input_dir = Path(input_dir)
        if not input_dir.exists() or not input_dir.is_dir():
            raise ValueError(f"Input directory not found: {input_dir}")

        # Get all image files using shared utility
        image_files = utils.list_image_files(input_dir, sort_by)

        if not image_files:
            raise ValueError(f"No image files found in directory: {input_dir}")

        return self.convert(image_files, output_path, **kwargs)
