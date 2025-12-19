import os

class DoclingIngest:
    def __init__(self):
        self.docling_available = False
        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
            self.docling_available = True
        except ImportError as e:
            print(f"DoclingIngest Warning: Docling not available (ImportError: {e}). Fallback to PyPDF enabled.")
            self.docling_available = False
        except Exception as e:
            print(f"DoclingIngest Warning: Docling init failed ({e}). Fallback to PyPDF enabled.")
            self.docling_available = False

    def process(self, file_path):
        """
        Converts a PDF/Document to markdown text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        print(f"Ingesting file: {file_path}")
        
        if self.docling_available:
            try:
                print("Attempting Docling conversion...")
                result = self.converter.convert(file_path)
                return result.document.export_to_markdown()
            except Exception as e:
                print(f"Docling conversion failed: {e}. Trying PyPDF fallback.")
        
        # Fallback to PyPDF
        return self._pypdf_fallback(file_path)

    def _pypdf_fallback(self, file_path):
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            return text
        except ImportError:
            return "Error: Neither Docling nor PyPDF is available. Please install 'pypdf'."
        except Exception as e:
            return f"Error reading PDF with PyPDF: {e}"
