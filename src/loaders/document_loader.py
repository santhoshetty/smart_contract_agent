from typing import List, Union
import os
from pathlib import Path
import pytesseract
from PIL import Image
import easyocr
from docx import Document
import PyPDF2

class DocumentLoader:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
    
    def load_document(self, file_path: Union[str, Path]) -> str:
        """Load and extract text from various document formats."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.txt']:
            return self._load_text(file_path)
        elif file_extension in ['.docx']:
            return self._load_docx(file_path)
        elif file_extension in ['.pdf']:
            return self._load_pdf(file_path)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            return self._load_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _load_text(self, file_path: Path) -> str:
        """Load text from .txt file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_docx(self, file_path: Path) -> str:
        """Load text from .docx file."""
        doc = Document(file_path)
        text_content = []

        # Process all document elements in order
        for element in doc.element.body:
            # If it's a paragraph
            if element.tag.endswith('p'):
                paragraph = element.text.strip()
                if paragraph:
                    text_content.append(paragraph)
            # If it's a table
            elif element.tag.endswith('tbl'):
                table = doc.tables[len([e for e in doc.element.body.iterchildren('w:tbl') if e.sourceline <= element.sourceline]) - 1]
                for row in table.rows:
                    # Get cell text and join with tabs for better formatting
                    row_text = '\t'.join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        text_content.append(row_text)

        return '\n'.join(text_content)
    
    def _load_pdf(self, file_path: Path) -> str:
        """Load text from PDF file."""
        text = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return '\n'.join(text)
    
    def _load_image(self, file_path: Path) -> str:
        """Load text from image using OCR."""
        # Try EasyOCR first
        result = self.reader.readtext(str(file_path))
        text = ' '.join([item[1] for item in result])
        
        # If EasyOCR fails or returns empty result, try Tesseract
        if not text.strip():
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
        
        return text 