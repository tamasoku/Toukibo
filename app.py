import streamlit as st
import pandas as pd
import io

st.title("Excel出力テスト（xlsxwriter 版）")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        st.success("CSV読み込み成功")
        st.dataframe(df.head())

        if df.empty:
            st.warning("⚠ データが空です。Excelは作れません。")
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  # ←ここを変更！
                df.to_excel(writer, index=False)
            output.seek(0)

            size = output.getbuffer().nbytes
            st.info(f"出力ファイルサイズ: {size} バイト")

            if size > 0:
                st.download_button(
                    label="Excelファイルをダウンロード",
                    data=output,
                    file_name="converted.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Excelファイルが空（0バイト）です。")

    except Exception as e:
        st.error(f"エラー: {e}")
