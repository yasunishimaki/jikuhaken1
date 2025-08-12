# -*- coding: utf-8 -*-
import os
import re
from typing import List, Tuple, Dict

from PyPDF2 import PdfReader

# pytesseract / PIL（未インストールでも落ちないように保護）
try:
    import pytesseract
    from PIL import Image
    # あなたの環境の実行ファイルを明示（この行は try ブロックの「中」に置く）
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\go832\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
except Exception:
    pytesseract = None
    Image = None

def _try_config_tesseract() -> str:
    """Tesseract本体の場所を推測。手動設定があればそれを使う。"""
    if pytesseract is None:
        return "pytesseract_not_installed"
    # すでに明示設定されている場合はそれを尊重
    cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", None)
    if cmd and os.path.exists(cmd):
        return cmd
    # よくあるパスも念のため探索
    common = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\go832\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract", "/usr/local/bin/tesseract", "/opt/homebrew/bin/tesseract",
    ]
    for p in common:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            return p
    return "tesseract_not_found"

def _clean(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def extract_text_from_pdf(path: str) -> str:
    parts: List[str] = []
    with open(path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                pass
    return _clean(" ".join(parts))

def extract_text_from_image(path: str, lang_hint: str = "jpn+eng") -> Tuple[str, str]:
    """戻り値: (テキスト, ステータス)"""
    if (pytesseract is None) or (Image is None):
        return "", "pytesseract_not_installed"
    status = _try_config_tesseract()
    try:
        img = Image.open(path)
        try:
            txt = pytesseract.image_to_string(img, lang=lang_hint)
        except Exception:
            # 日本語データが無い場合などは英語で再試行
            txt = pytesseract.image_to_string(img)
        return _clean(txt), status
    except Exception as e:
        return "", f"ocr_error:{e}"

def extract_from_paths(paths: List[str]) -> Tuple[str, List[Dict], List[str]]:
    """複数ファイルから抽出。戻り値: (連結テキスト, ソース情報, OCRステータス配列)"""
    aggregated = []
    sources = []
    ocr_status: List[str] = []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        if ext == ".pdf":
            txt = extract_text_from_pdf(p)
            sources.append({"path": p, "type": "pdf", "chars": len(txt)})
            aggregated.append(txt)
        elif ext in (".jpg", ".jpeg", ".png"):
            txt, st = extract_text_from_image(p)
            sources.append({"path": p, "type": "image", "chars": len(txt)})
            ocr_status.append(st)
            aggregated.append(txt)
        else:
            sources.append({"path": p, "type": "unsupported", "chars": 0})
    text = _clean(" ".join(aggregated))[:8000]  # 上限で切る
    return text, sources, ocr_status
