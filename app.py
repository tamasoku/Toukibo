import streamlit as st
import pandas as pd

st.title("CSV → CSV 出力テスト")

# CSVファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        # 読み込み（エンコーディングはshift_jisで調整）
        df = pd.read_csv(uploaded_file, encoding="shift_jis")
        st.success("CSV読み込み成功！")
        st.dataframe(df.head())  # 表示確認

        # ダウンロード用にCSV形式にエンコード
        csv_data = df.to_csv(index=False).encode("utf-8")

        # ダウンロードボタン
        st.download_button(
            label="このままCSVをダウンロード",
            data=csv_data,
            file_name="output.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"読み込みエラー: {e}")
