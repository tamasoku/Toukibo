import streamlit as st
import pandas as pd
from io import BytesIO

st.title("登記簿データ抽出ツール")
st.markdown("CSVファイルをアップロードし、名前でフィルタしてExcelファイルをダウンロードできます。")

# CSVファイルのアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    # CSVファイルを読み込み (Shift-JIS / UTF-8 自動判定)
    try:
        df = pd.read_csv(uploaded_file, encoding='shift_jis', dtype={'不動産番号': str})
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8', dtype={'不動産番号': str})
        except Exception:
            st.error("ファイルの読み込みに失敗しました。エンコードが正しくありません。")
            st.stop()
    else:
        pass  # 読み込み成功

    # 必要なカラムの存在チェック
    required_cols = ['権利部（甲区）氏名']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"必要なカラムがありません: {', '.join(missing)}")
        st.stop()

    # 空白行を補完
    df_filled = df.ffill()

    # 不動産番号を文字列形式で保持
    if '不動産番号' in df_filled.columns:
        df_filled['不動産番号'] = df_filled['不動産番号'].apply(lambda x: str(x))

    # データプレビュー
    with st.expander(f"アップロードデータプレビュー（全{len(df_filled)}件）"):
        st.dataframe(df_filled)

    # 名前の検索・フィルタ
    name_search = st.text_input("名前で検索（部分一致）", placeholder="例: 峯")
    names = df_filled['権利部（甲区）氏名'].unique()
    if name_search:
        names = [n for n in names if name_search in str(n)]

    selected_names = st.multiselect("フィルタする名前を選択してください", names)

    # 名前でフィルタリング
    if selected_names:
        filtered_df = df_filled[df_filled['権利部（甲区）氏名'].isin(selected_names)]

        # 名前と地番が重複する場合は、下段の行を保持する
        filtered_df = filtered_df.drop_duplicates(subset=['権利部（甲区）氏名', '地番'], keep='last')

        st.write(f"**{len(filtered_df)}件** がマッチしました")
        st.dataframe(filtered_df)

        # ダウンロードファイル名に所在を含める
        if '所在' in filtered_df.columns:
            locations = filtered_df['所在'].unique()
            location_str = '_'.join(str(loc).replace(' ', '') for loc in locations[:3])
            # ファイル名に使えない文字を除去
            for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                location_str = location_str.replace(ch, '')
            if len(locations) > 3:
                location_str += '_他'
            file_name = f"{location_str}.xlsx"
        else:
            file_name = "filtered_data.xlsx"

        # Excelファイルをメモリ上で作成
        def convert_df_to_excel(df_to_convert):
            output = BytesIO()
            df_to_convert.to_excel(output, index=False)
            return output.getvalue()

        excel_data = convert_df_to_excel(filtered_df)

        st.download_button(
            label=f"Excelファイルをダウンロード ({file_name})",
            data=excel_data,
            file_name=file_name,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
