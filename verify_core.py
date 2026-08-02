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
    print(f"Python：{sys.version.split()[0]}")
    print(f"環境：{sys.prefix}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
