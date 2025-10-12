import sys
from PIL import Image
import pytesseract

# Caminho do executável do Tesseract no Windows (ajuste se necessário)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Uso: python ocr_teste.py caminho/para/imagem.jpg (ou .png)
img = Image.open(sys.argv[1])
print(pytesseract.image_to_string(img, lang="por").strip())
