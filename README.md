# Smart Contract Populator Agent

An intelligent system that automatically generates contracts by extracting information from various document formats and populating a template.

## Features

- Multi-format document ingestion (PDF, DOCX, TXT, Images)
- OCR support for scanned documents
- Intelligent information extraction using LangChain
- Template-based contract generation
- Field validation and formatting
- Optional human-in-the-loop review

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configurations
   ```
4. Install Tesseract OCR:
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt-get install tesseract-ocr`
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

## Usage

1. Place your contract template in the `templates` directory
2. Run the Streamlit interface:
   ```bash
   streamlit run app.py
   ```
3. Upload your documents and generate contracts

## Project Structure

```
├── app.py                 # Streamlit interface
├── src/
│   ├── loaders/          # Document loaders
│   ├── processors/       # Text processing and OCR
│   ├── agents/          # LangChain agents
│   ├── validators/      # Field validation
│   └── generators/      # Contract generation
├── templates/           # Contract templates
└── tests/              # Test cases
```

## License

MIT License 