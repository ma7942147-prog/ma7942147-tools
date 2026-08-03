"""核心套件匯入驗證 — 依《1.AGENT_SETUP_教學檔案處理工具包.md》。

只做一次匯入驗證並回報結果，不做任何安裝或修復。
用法：.\\.venv\\Scripts\\python.exe verify_core.py
"""

import importlib
import sys

# (安裝名稱, 匯入名稱) — 這兩者常常不一樣，是新手最容易誤判「裝失敗」的地方
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

    for install_name, import_name in CORE:
        try:
            importlib.import_module(import_name)
        except Exception as exc:
            failed.append((install_name, import_name, exc))
            print(f"[X] {install_name:<34} import {import_name:<12} -> {type(exc).__name__}: {exc}")
        else:
            print(f"[OK] {install_name:<33} import {import_name}")

    ok = len(CORE) - len(failed)
    print()
    print(f"核心套件：{ok}/{len(CORE)} 匯入成功")
    print(f"Python：{sys.version.split()[0]}")
    print(f"執行檔：{sys.executable}")

    if failed:
        print()
        print("失敗清單（請回報原始錯誤，不要自動裝選用套件補救）：")
        for install_name, import_name, exc in failed:
            print(f"  - {install_name}（import {import_name}）：{type(exc).__name__}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
