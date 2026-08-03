#!/usr/bin/env python3
r"""核心工具包安裝驗證：只做一次匯入，回報哪些成功、哪些失敗。

來源：4.20260721,Agent_一鍵安裝檔.docx（三師爸 Sense Bar EP03）

用法：
    .\.venv\Scripts\python.exe verify_core.py

注意：部分套件的「安裝名稱」與「匯入名稱」不同，例如
    python-docx  -> import docx
    PyMuPDF      -> import fitz
    python-pptx  -> import pptx
    pillow       -> import PIL
"""

import importlib
import sys

# (安裝名稱, 匯入名稱, 用途)
CORE = [
    ("python-docx", "docx", "生成／讀寫 Word"),
    ("openpyxl", "openpyxl", "讀寫與格式化 Excel"),
    ("python-pptx", "pptx", "生成／改寫 PowerPoint"),
    ("pypdf", "pypdf", "PDF 合併、拆分、浮水印"),
    ("PyMuPDF", "fitz", "PDF 抽文字、抽頁、轉圖片"),
    ("reportlab", "reportlab", "生成 PDF 與浮水印圖層"),
    ("pillow", "PIL", "圖片裁切、去白邊、合成"),
    ("matplotlib", "matplotlib", "產生統計圖表"),
    ("qrcode[pil]", "qrcode", "產生 QR Code"),
    ("markitdown[pdf,docx,pptx,xlsx]", "markitdown", "文件轉 Markdown"),
]


def main():
    print(f"Python：{sys.version.split()[0]}")
    print(f"直譯器：{sys.executable}\n")

    failed = []
    for install_name, import_name, purpose in CORE:
        try:
            mod = importlib.import_module(import_name)
            ver = getattr(mod, "__version__", "")
            ver = f"  {ver}" if ver else ""
            print(f"  OK   {install_name:<32} (import {import_name}){ver}")
        except Exception as e:
            failed.append((install_name, import_name, e))
            print(f"  失敗 {install_name:<32} (import {import_name})  {type(e).__name__}: {e}")

    total = len(CORE)
    ok = total - len(failed)
    print(f"\n核心套件：{ok}/{total} 匯入成功")

    if failed:
        print("\n失敗清單：")
        for install_name, import_name, e in failed:
            print(f"  - {install_name}（import {import_name}）：{type(e).__name__}: {e}")
        print("\n請把上面的原始錯誤回報，不要靠安裝選用套件來補救。")
        return 1

    # markitdown 最常見的坑是「裝了但沒帶 extras」。
    # 光 import markitdown 看不出來，連 MarkItDown() 裡的轉換器清單也看不出來——
    # 轉換器類別永遠會註冊，缺 extras 只會在真的轉檔時才丟 MissingDependencyException。
    # 所以這裡直接檢查每個 extra 實際帶進來的相依套件在不在。
    EXTRA_DEPS = [
        ("pdf", "pdfminer", "pdfminer-six"),
        ("docx", "mammoth", "mammoth"),
        ("xlsx", "pandas", "pandas"),
        ("pptx", "pptx", "python-pptx"),
    ]
    missing = []
    for extra, module, pkg in EXTRA_DEPS:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(f"{extra}（缺 {pkg}）")

    if missing:
        print(f"\n注意：markitdown 少了這些 extras：{', '.join(missing)}")
        print("      八成是裝成裸的 markitdown。轉檔時才會爆 MissingDependencyException。請改裝：")
        print('      uv pip install --python .\\.venv\\Scripts\\python.exe "markitdown[pdf,docx,pptx,xlsx]"')
        return 1

    print("markitdown extras：pdf、docx、pptx、xlsx 四組相依套件都在")
    return 0


if __name__ == "__main__":
    sys.exit(main())
