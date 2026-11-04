from pathlib import Path
import io
import re
import fitz
import pandas as pd
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
from .config import TESSERACT_CMD

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

class DocumentReadError(Exception):
    pass

def _ocr_image(image: Image.Image) -> str:
    # A light preprocessing pass helps with low-contrast scans without changing the source file.
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.4)
    image = image.filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(image, config="--psm 6")

def read_pdf(path: Path) -> str:
    pages = []
    try:
        with fitz.open(path) as pdf:
            if pdf.page_count == 0:
                raise DocumentReadError("The PDF contains no pages.")
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                if len(text) < 20:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = _ocr_image(image).strip()
                pages.append(f"[Page {page_number}]\n{text}")
    except DocumentReadError:
        raise
    except Exception as exc:
        raise DocumentReadError(f"Could not read PDF: {exc}") from exc
    return "\n\n".join(pages)

def read_image(path: Path) -> str:
    try:
        with Image.open(path) as image:
            frames = []
            frame_count = getattr(image, "n_frames", 1)
            for index in range(frame_count):
                image.seek(index)
                frames.append(f"[Image page {index + 1}]\n{_ocr_image(image.copy()).strip()}")
            return "\n\n".join(frames)
    except Exception as exc:
        raise DocumentReadError(f"Could not process image: {exc}") from exc

def read_spreadsheet(path: Path) -> str:
    try:
        ext = path.suffix.lower()
        if ext == ".csv":
            frames = {"CSV": pd.read_csv(path, dtype=str, keep_default_na=False)}
        else:
            frames = pd.read_excel(path, sheet_name=None, dtype=str, keep_default_na=False)
        chunks = []
        for sheet_name, frame in frames.items():
            chunks.append(f"[Sheet: {sheet_name}]\n{frame.to_csv(index=False)}")
        return "\n\n".join(chunks)
    except Exception as exc:
        raise DocumentReadError(f"Could not parse spreadsheet: {exc}") from exc

def extract_document_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf(path)
    if ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        return read_image(path)
    if ext in {".xlsx", ".xls", ".csv"}:
        return read_spreadsheet(path)
    raise DocumentReadError(f"Unsupported file type: {ext}")
