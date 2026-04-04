"""Merge multiple PDF files into one."""

from pathlib import Path
from typing import Optional, Dict, Sequence, Any
import fitz

from . import utils


class PDFMerger:
    """Merge multiple PDF files into a single PDF."""

    def merge(
        self,
        input_files: Sequence[Path | str],
        output_path: Path | str,
        page_ranges: Optional[Dict[int, str]] = None,
        add_bookmarks: bool = True,
        overwrite: bool = False,
    ) -> Dict[str, int]:
        """Merge PDFs.

        Args:
            input_files: List of input PDF files
            output_path: Path for the merged output
            page_ranges: Optional dict mapping input file index to page range string
            add_bookmarks: Whether to add bookmarks for each input file
            overwrite: Whether to overwrite existing output file

        Returns:
            Dict with total_pages in output

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        for i, input_file in enumerate(input_files):
            valid, error = utils.validate_pdf_file(input_file)
            if not valid:
                raise ValueError(error)

        valid, error = utils.validate_output_path(output_path, overwrite)
        if not valid:
            raise ValueError(error)

        output_path = Path(output_path)
        page_ranges = page_ranges or {}

        # Create output document
        output_doc = fitz.open()
        total_pages = 0
        toc = []

        for idx, input_file in enumerate(input_files):
            input_path = Path(input_file)
            input_doc = fitz.open(input_path)

            # Get page range for this file
            range_str = page_ranges.get(idx, "")
            if range_str:
                pages = utils.parse_page_ranges(range_str, len(input_doc))
            else:
                pages = list(range(len(input_doc)))

            # Add pages to output
            if len(pages) > 0:
                output_doc.insert_pdf(input_doc, from_page=pages[0], to_page=pages[-1])
                total_pages += len(pages)

            # Add bookmark if requested
            if add_bookmarks and len(pages) > 0:
                bookmark_name = input_path.stem
                # TOC entry: (level, title, page) - page is 1-indexed in output
                output_start_page = total_pages - len(pages) + 1
                toc.append([1, bookmark_name, output_start_page])

            input_doc.close()

        # Set table of contents if we have bookmarks
        if add_bookmarks and toc:
            output_doc.set_toc(toc)

        # Save output
        output_doc.save(output_path, garbage=4, deflate=True)
        output_doc.close()

        return {"total_pages": total_pages, "input_files": len(input_files)}


def merge_pdfs(
    input_files: Sequence[str | Path], output_path: str | Path, **kwargs: Any
) -> Dict[str, int]:
    """Convenience function to merge PDFs.

    Args:
        input_files: List of input PDF paths
        output_path: Output merged PDF path
        **kwargs: Additional arguments for PDFMerger.merge

    Returns:
        Dict with result information
    """
    merger = PDFMerger()
    return merger.merge(input_files, output_path, **kwargs)
