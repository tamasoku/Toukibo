import re

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

    # 物件特定カラムのみ前方補完（権利部カラムはffillしない）
    # → 区分所有等で権利部が空の行に、前の行の所有者が誤って入るのを防ぐ
    property_cols = ['不動産番号', '所在', '地番', '地目', '地積']
    property_cols = [c for c in property_cols if c in df.columns]
    df_filled = df.copy()
    df_filled[property_cols] = df[property_cols].ffill()

    # 不動産番号を文字列形式で保持
    if '不動産番号' in df_filled.columns:
        df_filled['不動産番号'] = df_filled['不動産番号'].apply(lambda x: str(x))

    # 各地番の現所有者を抽出
    # 「登記の目的」カラムがある場合:
    #   所有権移転/所有権登記 → 全員入れ替え
    #   X持分全部移転 → Xを除外し新しい人を追加
    #   X持分一部移転 → Xは残し新しい人を追加
    # ない場合: 最後の「原因あり」行から末尾まで（フォールバック）
    def extract_current_owners(df_src):
        has_chiban_col = '地番' in df_src.columns
        has_purpose_col = '権利部（甲区）登記の目的' in df_src.columns
        has_junni_col = '権利部（甲区）順位番号' in df_src.columns
        has_cause_col = '権利部（甲区）原因' in df_src.columns

        if not has_chiban_col:
            return df_src.dropna(subset=['権利部（甲区）氏名'])

        results = []
        for _, group in df_src.groupby('地番', sort=False):
            # 敷地権化された土地の判定: 登記の目的が「所有権敷地権」のみの場合
            if has_purpose_col:
                purposes = group['権利部（甲区）登記の目的'].dropna().unique()
                if len(purposes) == 1 and purposes[0] == '所有権敷地権':
                    row = group.iloc[0].copy()
                    row['権利部（甲区）氏名'] = '所有権敷地権'
                    results.append(pd.DataFrame([row]))
                    continue

            named = group.dropna(subset=['権利部（甲区）氏名'])
            if named.empty:
                continue

            # 順位番号＋登記の目的がある場合: 持分移転を追跡して正確に判定
            if has_purpose_col and has_junni_col:
                work = named.copy()
                work['権利部（甲区）順位番号'] = work['権利部（甲区）順位番号'].ffill()
                if has_cause_col:
                    work['権利部（甲区）原因'] = work['権利部（甲区）原因'].ffill()
                current_rows = {}
                for _, entry_group in work.groupby('権利部（甲区）順位番号', sort=False):
                    purpose = str(entry_group.iloc[0].get('権利部（甲区）登記の目的', ''))
                    new_rows = {}
                    for idx, row in entry_group.iterrows():
                        new_rows[row['権利部（甲区）氏名']] = row

                    if purpose in ('所有権移転', '所有権登記', '合併による所有権登記') or '共有者全員持分全部移転' in purpose:
                        current_rows = new_rows.copy()
                    else:
                        match = re.match(r'(.+?)持分(全部|一部)(?:（[^）]*）)?移転', purpose)
                        if match:
                            person, transfer_type = match.group(1), match.group(2)
                            if transfer_type == '全部':
                                current_rows.pop(person, None)
                            current_rows.update(new_rows)
                        else:
                            current_rows.update(new_rows)

                if current_rows:
                    results.append(pd.DataFrame(list(current_rows.values())))
                continue

            # フォールバック: 原因カラムベースの判定
            if has_cause_col:
                has_cause = named[named['権利部（甲区）原因'].notna()]
                if not has_cause.empty:
                    last_cause_idx = has_cause.index[-1]
                    results.append(named.loc[named.index >= last_cause_idx])
                    continue

            results.append(named.tail(1))

        if results:
            return pd.concat(results)
        return pd.DataFrame(columns=df_src.columns)

    df_current = extract_current_owners(df_filled)

    # データプレビュー
    with st.expander(f"アップロードデータプレビュー（全{len(df_filled)}件）"):
        st.dataframe(df_filled)

    # 名前フィルタ（現所有者のみ）
    names = df_current['権利部（甲区）氏名'].unique()
    st.markdown("※現所有者全ての場合は「Select all」を選択ください")
    selected_names = st.multiselect("フィルタする名前を選択してください", names)

    # 出力から除外するカラム（ロジック用のみ）
    exclude_cols = ['権利部（甲区）順位番号', '権利部（甲区）登記の目的', '権利部（甲区）種類']
    output_cols = [c for c in df_current.columns if c not in exclude_cols]

    # 名前でフィルタリング
    if selected_names:
        filtered_df = df_current[df_current['権利部（甲区）氏名'].isin(selected_names)][output_cols]

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
            file_name = f"{location_str}_JUSTDB用.xlsx"
        else:
            file_name = "filtered_data_JUSTDB用.xlsx"

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
