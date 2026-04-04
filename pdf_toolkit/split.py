"""Split a PDF into multiple files."""

from pathlib import Path
from typing import List, Dict
import fitz

from . import utils


class PDFSplitter:
    """Split a PDF into multiple files."""

    def split_by_pages(
        self,
        input_file: Path | str,
        output_dir: Path | str,
        pages_per_file: int = 1,
        prefix: str = "",
        overwrite: bool = False,
    ) -> List[Dict[str, int | str]]:
        """Split PDF into multiple files with fixed pages per file.

        Args:
            input_file: Input PDF file
            output_dir: Output directory
            pages_per_file: Number of pages per output file
            prefix: Prefix for output filenames
            overwrite: Whether to overwrite existing files

        Returns:
            List of result info for each output file
        """
        # Validate input
        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if pages_per_file < 1:
            raise ValueError("pages_per_file must be at least 1")

        input_path = Path(input_file)
        if not prefix:
            prefix = input_path.stem

        doc = fitz.open(input_path)
        total_pages = len(doc)
        results: List[Dict[str, int | str]] = []

        for file_idx, start_page in enumerate(range(0, total_pages, pages_per_file)):
            end_page = min(start_page + pages_per_file - 1, total_pages - 1)
            num_pages = end_page - start_page + 1

            # Generate output filename
            if pages_per_file == 1:
                output_filename = f"{prefix}_page_{start_page + 1}.pdf"
            else:
                output_filename = f"{prefix}_part_{file_idx + 1}.pdf"

            output_path = output_dir / output_filename

            if output_path.exists() and not overwrite:
                doc.close()
                raise ValueError(f"Output file already exists: {output_path}")

            # Create new document
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()

            results.append(
                {
                    "output_path": str(output_path),
                    "start_page": start_page + 1,  # 1-indexed
                    "end_page": end_page + 1,
                    "pages": num_pages,
                }
            )

        doc.close()
        return results

    def split_by_ranges(
        self,
        input_file: Path | str,
        output_dir: Path | str,
        ranges: List[str],
        prefix: str = "",
        overwrite: bool = False,
    ) -> List[Dict[str, int | str]]:
        """Split PDF by custom page ranges.

        Args:
            input_file: Input PDF file
            output_dir: Output directory
            ranges: List of page range strings (e.g., ["1-5", "6-10"])
            prefix: Prefix for output filenames
            overwrite: Whether to overwrite existing files

        Returns:
            List of result info for each output file
        """
        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        input_path = Path(input_file)
        if not prefix:
            prefix = input_path.stem

        doc = fitz.open(input_path)
        total_pages = len(doc)
        results: List[Dict[str, int | str]] = []

        for idx, range_str in enumerate(ranges):
            pages = utils.parse_page_ranges(range_str, total_pages)

            if not pages:
                continue

            output_filename = f"{prefix}_{range_str.replace(',', '_')}.pdf"
            output_path = output_dir / output_filename

            if output_path.exists() and not overwrite:
                doc.close()
                raise ValueError(f"Output file already exists: {output_path}")

            new_doc = fitz.open()
            # Insert pages in order
            for page_num in pages:
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()

            results.append(
                {
                    "output_path": str(output_path),
                    "range": range_str,
                    "pages": len(pages),
                }
            )

        doc.close()
        return results

    def extract_pages(
        self,
        input_file: Path | str,
        output_path: Path | str,
        page_ranges: str,
        overwrite: bool = False,
    ) -> Dict[str, int | str]:
        """Extract specific pages to a single output file.

        Args:
            input_file: Input PDF file
            output_path: Output PDF file
            page_ranges: Page range string
            overwrite: Whether to overwrite existing file

        Returns:
            Result info
        """
        valid, error = utils.validate_pdf_file(input_file)
        if not valid:
            raise ValueError(error)

        valid, error = utils.validate_output_path(output_path, overwrite)
        if not valid:
            raise ValueError(error)

        output_path = Path(output_path)
        doc = fitz.open(input_file)
        total_pages = len(doc)
        pages = utils.parse_page_ranges(page_ranges, total_pages)

        if not pages:
            doc.close()
            raise ValueError("No valid pages specified")

        new_doc = fitz.open()
        for page_num in pages:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        new_doc.save(output_path, garbage=4, deflate=True)
        new_doc.close()
        doc.close()

        return {"output_path": str(output_path), "pages_extracted": len(pages)}
