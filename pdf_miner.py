# pip install pdfminer.six

from pdfminer.high_level import extract_text

pdf_path = "02.pdf"  # caminho do seu arquivo

texto = extract_text(pdf_path) or ""
print(texto)
