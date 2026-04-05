---
title: PDF Toolkit
emoji: 📄
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# PDF Toolkit

A comprehensive Python PDF toolkit with all essential PDF processing features:

- **Merge** - Combine multiple PDF files into one
- **Split** - Split PDF into multiple files
- **Extract** - Extract specific pages from PDF
- **Compress** - Reduce PDF file size
- **PDF to Image** - Convert PDF pages to PNG/JPEG images
- **Image to PDF** - Convert image files to PDF
- **Compare** - Compare two PDFs with visual difference highlighting

## Features

This is a web-based demo of the PDF Toolkit. Try it out by uploading your PDFs and using the different operations!

All processing happens on the server - no data is stored permanently.

## Command Line Usage

This project is also available as a command-line tool. See the [GitHub repository](https://github.com/EthanDai-1205/PDF-Toolkit) for full documentation.

## Requirements

- Python 3.9+
- (Optional) Ghostscript for better PDF compression - already installed on this Space

## Libraries Used

- **PyMuPDF (fitz)** - Core PDF manipulation (fast, C-backed)
- **Pillow** - Image processing
- **OpenCV** - Visual difference detection for comparison
- **Gradio** - Web interface
- **Click** - Command-line interface
