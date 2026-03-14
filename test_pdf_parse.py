"""
登記簿PDF読み取り検証スクリプト

使い方:
  pip install pdfplumber
  python test_pdf_parse.py <PDFファイルパス>

登記簿PDFからテキストを抽出し、構造化できるか検証します。
"""

import sys
import pdfplumber


def extract_text_from_pdf(pdf_path):
    """PDFから全ページのテキストを抽出"""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        print(f"総ページ数: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            pages_text.append(text or "")
            print(f"\n{'='*60}")
            print(f"ページ {i+1}")
            print(f"{'='*60}")
            print(text or "(テキストなし)")
    return pages_text


def extract_tables_from_pdf(pdf_path):
    """PDFからテーブル構造を抽出"""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                print(f"\n{'='*60}")
                print(f"ページ {i+1} のテーブル ({len(tables)}個)")
                print(f"{'='*60}")
                for j, table in enumerate(tables):
                    print(f"\n--- テーブル {j+1} ---")
                    for row in table:
                        print(row)
            else:
                print(f"ページ {i+1}: テーブルなし")


def main():
    if len(sys.argv) < 2:
        print("使い方: python test_pdf_parse.py <PDFファイルパス>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"ファイル: {pdf_path}")

    print("\n" + "#"*60)
    print("# テキスト抽出結果")
    print("#"*60)
    extract_text_from_pdf(pdf_path)

    print("\n" + "#"*60)
    print("# テーブル抽出結果")
    print("#"*60)
    extract_tables_from_pdf(pdf_path)


if __name__ == "__main__":
    main()
