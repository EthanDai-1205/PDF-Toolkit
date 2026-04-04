"""Tests for utils module."""

from pdf_toolkit.utils import validate_pdf_file, parse_page_ranges


def test_validate_pdf_file_not_exists():
    valid, error = validate_pdf_file("nonexistent.pdf")
    assert not valid
    assert "not found" in error


def test_validate_pdf_file_wrong_extension(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.touch()
    valid, error = validate_pdf_file(txt_file)
    assert not valid
    assert "Not a PDF" in error


def test_parse_page_ranges_single_page():
    result = parse_page_ranges("5", 10)
    assert result == [4]  # 0-indexed


def test_parse_page_ranges_range():
    result = parse_page_ranges("1-5", 10)
    assert result == [0, 1, 2, 3, 4]


def test_parse_page_ranges_multiple_ranges():
    result = parse_page_ranges("1-3,5-7", 10)
    assert result == [0, 1, 2, 4, 5, 6]


def test_parse_page_ranges_start_open():
    result = parse_page_ranges("-3", 10)
    assert result == [0, 1, 2]


def test_parse_page_ranges_end_open():
    result = parse_page_ranges("8-", 10)
    # 8-10 inclusive -> 7, 8, 9 (0-indexed)
    assert result == [7, 8, 9]


def test_parse_page_ranges_comma_separated():
    result = parse_page_ranges("1,3,5", 10)
    assert result == [0, 2, 4]


def test_parse_page_ranges_with_spaces():
    result = parse_page_ranges("1 - 3 , 5", 10)
    assert result == [0, 1, 2, 4]
