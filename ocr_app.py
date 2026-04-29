import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd

from api_functions import extract_text_from_image, structure_text_with_gemini

# --- 1. 環境設定と初期化 ---
load_dotenv(".env_app")
CSV_FILE = os.getenv("CSV_FILE")


# セッションステート（一時保存リスト）の初期化
if "scanned_list" not in st.session_state:
    st.session_state["scanned_list"] = []

# ==========================================
# 2. Streamlit UIの実装
# ==========================================
st.set_page_config(page_title="名簿OCRツール", layout="wide")
st.title("📷 名簿デジタル化（OCR → CSV）ツール")


tabs = st.tabs(["画像データ", "データの出力(CSV)"])


with tabs[0]:
    st.header("1. 画像読み込みと修正")
    st.markdown(
        "画像からテキストを読み取り、初期データを生成します。**必ず目視で確認し、必要に応じて修正してください。**"
    )

    uploaded_file = st.file_uploader(
        "申込書の画像をアップロード", type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("入力画像")
            st.image(uploaded_file, width="stretch")

        with col2:
            st.subheader("データ抽出と確認")

            if st.button("データを読み取る", type="primary"):
                with st.spinner("Vision APIでテキストを抽出中..."):
                    image_bytes = uploaded_file.getvalue()
                    try:
                        raw_text = extract_text_from_image(image_bytes)
                    except Exception as e:
                        st.error(f"OCR処理に失敗しました: {e}")
                        st.stop()

                with st.spinner("Gemini APIでデータを構造化中..."):
                    try:
                        structured_data = structure_text_with_gemini(raw_text)
                        st.session_state["extracted_data"] = structured_data
                        st.success("抽出完了！内容を確認・修正してください。")
                    except Exception as e:
                        st.error(f"Gemini API: 構造化処理に失敗しました: {e}")
                        st.stop()

            # セッションにデータがある場合、修正UI（Data Editor）を表示
            if "extracted_data" in st.session_state:
                st.markdown("#### 修正フォーム")
                st.info("以下の表のセルをクリックすると、直接値を修正できます。")

                # st.data_editorを使用して、人間が直接修正できるUIを提供
                edited_data = st.data_editor(
                    st.session_state["extracted_data"],
                    num_rows="fixed",
                    width="stretch",
                    column_config={"value": st.column_config.TextColumn("抽出値")},
                )
                print(edited_data)
                st.markdown("---")
                if st.button("この内容で登録（リストに追加）"):
                    # ここにデータベースやCSVへの保存処理を記述します
                    st.session_state["scanned_list"].append(edited_data.copy())
                    st.success("以下のデータで登録処理を実行しました。")
                    st.json(edited_data)

                    # 次の画像のために原文をクリア
                    del st.session_state["extracted_data"]
                    st.rerun()

with tabs[1]:
    st.header("2. 出力待ちリスト")
    if len(st.session_state["scanned_list"]) > 0:
        df_export = pd.DataFrame(st.session_state["scanned_list"])

        # 編集可能なテーブルで最終確認
        edited_df = st.data_editor(
            df_export,
            num_rows="dynamic",
            width="stretch",
        )

        st.write(f"現在 **{len(edited_df)}件** のデータが待機中です。")

        csv_data = edited_df.to_csv(index=False).encode("utf-8-sig")  # UTF-8 BOM付き

        st.download_button(
            label="このリストをCSVでダウンロード",
            data=csv_data,
            file_name=CSV_FILE,
            mime="text/csv",
            type="primary",
        )

        if st.button("リストをすべてクリア", type="secondary"):
            st.session_state["scanned_list"] = []
            st.rerun()
    else:
        st.info("現在追加されているデータはありません。")
