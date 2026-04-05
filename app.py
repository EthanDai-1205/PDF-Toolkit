"""PDF Toolkit Gradio app entry point for Hugging Face Spaces."""
from pdf_toolkit.app import create_app

app = create_app()

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0")
