import sys, os, re
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import ImageOps, Image, ImageFilter

# Caminhos no Windows (ajuste se necessário)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER = r"C:\Program Files\poppler-25.07.0\Library\bin"  # deixe "" se estiver no PATH

def _otsu_threshold(g):
    hist = g.histogram()
    total = sum(hist)
    sumB = wB = best = 0
    sum1 = sum(i * h for i, h in enumerate(hist))
    for i in range(256):
        wB += hist[i]
        if wB == 0: 
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += i * hist[i]
        mB = sumB / wB
        mF = (sum1 - sumB) / wF
        between = wB * wF * (mB - mF) ** 2
        if between > best:
            best, thr = between, i
    return thr

def _deskew_osd(img):
    try:
        osd = pytesseract.image_to_osd(img)
        m = re.search(r"Rotate:\s+(\d+)", osd)
        angle = int(m.group(1)) if m else 0
        if angle:
            img = img.rotate(-angle, expand=True, resample=Image.BICUBIC)
    except Exception:
        pass
    return img

def _ocr_img_pt(img):
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g)
    g = g.filter(ImageFilter.MedianFilter(size=3))
    if max(g.size) < 2000:
        g = g.resize((g.width*2, g.height*2), Image.LANCZOS)
    g = _deskew_osd(g)
    try:
        t = _otsu_threshold(g)
        g = g.point(lambda p: 255 if p > t else 0)
    except Exception:
        pass
    texts = []
    for psm in (6, 11, 4):  # 6=bloco, 11=sparse, 4=colunas
        cfg = f"--oem 3 --psm {psm}"
        txt = pytesseract.image_to_string(g, lang="por", config=cfg).strip()
        texts.append(txt)
    return max(texts, key=len, default="").strip()

def main():
    if len(sys.argv) < 2:
        print("Uso: python pdf.py arquivo.pdf [--force-ocr]", file=sys.stderr); return
    pdf = sys.argv[1]
    force_ocr = "--force-ocr" in sys.argv

    txt = ""
    if not force_ocr:
        try:
            r = PdfReader(pdf)
            txt = "\n".join((p.extract_text() or "") for p in r.pages).strip()
        except Exception as e:
            print(f"[warn] Falha na extração nativa: {e}", file=sys.stderr)

    if txt:
        print(txt); return

    try:
        imgs = convert_from_path(pdf, dpi=450, poppler_path=(POPPLER or None))
    except Exception as e:
        print("Erro ao rasterizar PDF (Poppler).", file=sys.stderr)
        print(f"Detalhe: {e}", file=sys.stderr)
        sys.exit(1)

    pages = [_ocr_img_pt(im) for im in imgs]
    ocr_txt = "\n\n".join(p for p in pages if p).strip()
    print(ocr_txt if ocr_txt else "[sem texto reconhecido]", file=(sys.stdout if ocr_txt else sys.stderr))
    if not ocr_txt:
        sys.exit(2)

if __name__ == "__main__":
    main()