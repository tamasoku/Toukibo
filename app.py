import streamlit as st
import pandas as pd
import io

st.title("Excel出力テスト")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis')
        st.success("CSV読み込み成功")
        st.write(f"データ件数: {len(df)} 行 / {len(df.columns)} 列")
        st.dataframe(df.head())

        if df.empty:
            st.warning("⚠ データが空です。Excelは作れません。")
        else:
            # Excelに変換
            output = io.BytesIO()
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)
                file_size = output.getbuffer().nbytes
                st.info(f"出力されたExcelファイルのサイズ: {file_size} バイト")

                if file_size > 0:
                    st.download_button(
                        label="Excelをダウンロード",
                        data=output,
                        file_name="converted.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("❌ Excelバッファが0バイトです。to_excel() が失敗している可能性あり。")

            except Exception as e:
                st.error(f"Excel変換中の例外: {e}")
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
