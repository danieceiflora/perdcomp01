import os
import sys
from pdfminer.high_level import extract_text as pdfminer_extract_text


def extract_text(pdf_path: str) -> str:
    """Extrai texto diretamente de um PDF utilizando pdfminer.six (melhor extração)."""
    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("Somente arquivos PDF são suportados")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    try:
        text = pdfminer_extract_text(pdf_path) or ""
        return text.strip()
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}", file=sys.stderr)
        return ""

def main():
    if len(sys.argv) < 2:
        print("Uso: python pdf.py arquivo.pdf", file=sys.stderr); return
    pdf = sys.argv[1]
    try:
        txt = extract_text(pdf)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)

    if not txt:
        print("[sem texto reconhecido]", file=sys.stderr)
        sys.exit(2)

    print(txt)

if __name__ == "__main__":
    main()