# Default Corpus Folder

This is the default location for your document corpus in Ashurbanipal.

## Usage

You can:

1. Copy documents directly into this folder
2. Use the web interface to ingest folders
3. Upload individual files through the UI

## Supported Formats

- PDF files (.pdf)
- Microsoft Word documents (.docx, .doc)
- Text files (.txt)
- Markdown files (.md)
- Rich Text Format (.rtf)

## Note

Source code files (Python, JavaScript, etc.) are automatically filtered out to keep your corpus focused on documents rather than code.

To change the default corpus location, modify the `DEFAULT_CORPUS_PATH` in `backend/config.py`.
