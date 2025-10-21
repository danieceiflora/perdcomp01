import os
import sys
from pypdf import PdfReader


def extract_text(pdf_path: str) -> str:
    """Extrai texto diretamente de um PDF utilizando apenas o conteúdo embutido."""
    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("Somente arquivos PDF são suportados")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    reader = PdfReader(pdf_path)
    texts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        texts.append(page_text)

    return "\n".join(texts).strip()

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