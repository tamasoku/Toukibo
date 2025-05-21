import streamlit as st
import pandas as pd

# openpyxlを使ってExcelファイルを保存する
import openpyxl

# CSVファイルのアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    # CSVファイルを読み込み (Shift-JISエンコーディングを指定)
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis', dtype={'不動産番号': str})  # 不動産番号を文字列として読み込む
    except UnicodeDecodeError:
        st.error("ファイルの読み込みに失敗しました。エンコードが正しくありません。")
    else:
        # 空白行を補完
        df_filled = df.fillna(method='ffill')

        # 不動産番号を文字列形式で保持
        if '不動産番号' in df_filled.columns:
            df_filled['不動産番号'] = df_filled['不動産番号'].apply(lambda x: str(x))

        # 名前の選択
        names = df_filled['権利部（甲区）氏名'].unique()
        selected_names = st.multiselect("フィルタする名前を選択してください", names)

        # 名前でフィルタリング
        if selected_names:
            filtered_df = df_filled[df_filled['権利部（甲区）氏名'].isin(selected_names)]

            # 名前と地番が重複する場合は、下段の行を保持する
            filtered_df = filtered_df.drop_duplicates(subset=['権利部（甲区）氏名', '地番'], keep='last')

            st.dataframe(filtered_df)

            # Excelファイルとしてダウンロード (Excel形式でエクスポート)
            @st.cache
            def convert_df_to_excel(df):
                return df.to_excel('filtered_data.xlsx', index=False)

            # Excelファイルを作成
            convert_df_to_excel(filtered_df)

            with open('filtered_data.xlsx', 'rb') as file:
                st.download_button(
                    label="Excelファイルをダウンロード",
                    data=file,
                    file_name='filtered_data.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
