r"""核心套件匯入驗證：只做一次匯入，回報成功／失敗清單。

用法（Windows）：.\.venv\Scripts\python.exe verify_core.py
"""

import importlib
import sys

# (安裝名稱, 匯入名稱) —— 兩者不同的地方是新手最常誤判失敗的原因
CORE = [
    ("python-docx", "docx"),
    ("openpyxl", "openpyxl"),
    ("python-pptx", "pptx"),
    ("pypdf", "pypdf"),
    ("PyMuPDF", "fitz"),
    ("reportlab", "reportlab"),
    ("pillow", "PIL"),
    ("matplotlib", "matplotlib"),
    ("qrcode[pil]", "qrcode"),
    ("markitdown[pdf,docx,pptx,xlsx]", "markitdown"),
]


# 指南列為「選用」但可能被 markitdown extras 當相依套件拖進來的東西。
# 這裡不判對錯，只如實回報，避免印出「選用套件：未安裝」這種與事實不符的話。
OPTIONAL = [
    ("pandas", "pandas"),
    ("pdfplumber", "pdfplumber"),
    ("pytesseract", "pytesseract"),
    ("ocrmypdf", "ocrmypdf"),
    ("pdf2image", "pdf2image"),
]


def main() -> int:
    failed = []
    for package, module in CORE:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 — 要看見原始錯誤才好判斷
            failed.append((package, module, exc))
            print(f"❌ {package:<32} import {module} —— {type(exc).__name__}: {exc}")
        else:
            print(f"✅ {package:<32} import {module}")

    ok = len(CORE) - len(failed)
    print(f"\n核心套件：{ok}/{len(CORE)} 匯入成功")

    present = []
    for package, module in OPTIONAL:
        try:
            importlib.import_module(module)
        except Exception:  # noqa: BLE001 — 這裡不在乎為什麼載不進來，沒有就是沒有
            continue
        present.append(package)

    if present:
        print(f"💡 選用套件：未主動安裝，但被相依帶進來 → {', '.join(present)}")
        print("   （markitdown[xlsx] 會帶 pandas、markitdown[pdf] 會帶 pdfplumber，屬正常）")
    else:
        print("💡 選用套件：未安裝")

    print(f"Python：{sys.version.split()[0]}")
    print(f"環境：{sys.prefix}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
