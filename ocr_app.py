import streamlit as st
import pandas as pd
from google.cloud import vision
import os
from dotenv import load_dotenv

# 環境変数の読み込み (.envにAPIキーパスを設定)
load_dotenv()

# セッションステート（一時保存リスト）の初期化
if 'scanned_list' not in st.session_state:
    st.session_state['scanned_list'] = []

def detect_text(content):
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image, image_context={"language_hints": ["ja"]})
        return response.full_text_annotation.text if response.full_text_annotation else ""
    except Exception as e:
        st.error(f"OCRエラー: {e}\n(APIキーが正しく設定されているか確認してください)")
        return ""

st.set_page_config(page_title="名簿OCRツール", layout="wide")
st.title("📷 名簿デジタル化（OCR → CSV）ツール")

col_ocr, col_list = st.columns([1, 1])

with col_ocr:
    st.header("1. 画像読み込みと修正")
    uploaded_file = st.file_uploader("名簿のスキャン画像を選択", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        if st.button("OCRで文字を抽出"):
            with st.spinner("Google Cloud Vision で解析中..."):
                st.session_state['ocr_raw'] = detect_text(uploaded_file.getvalue())
        
        if 'ocr_raw' in st.session_state:
            with st.form("ocr_entry_form"):
                st.write("解析結果を元にデータを整形してください:")
                n_name = st.text_input("氏名 (name)")
                n_zip = st.text_input("郵便番号 (zip_code)")
                n_addr = st.text_input("住所 (address)")
                n_tel = st.text_input("電話番号 (tel)")
                n_fee = st.number_input("会費 (fee)", value=0)
                n_comment = st.text_area("備考 (comment)", value="OCR登録", height=68)
                
                with st.expander("OCRの原文を見る"):
                    st.text(st.session_state['ocr_raw'])
                
                if st.form_submit_button("リストに追加"):
                    # 一時リストに追加
                    st.session_state['scanned_list'].append({
                        "name": n_name,
                        "zip_code": n_zip,
                        "address": n_addr,
                        "tel": n_tel,
                        "fee": n_fee,
                        "comment": n_comment
                    })
                    st.success(f"{n_name} さんをリストに追加しました！続けて次の画像を処理できます。")
                    # 次の画像のために原文をクリア
                    del st.session_state['ocr_raw']
                    st.rerun()

with col_list:
    st.header("2. 出力待ちリスト")
    if len(st.session_state['scanned_list']) > 0:
        df_export = pd.DataFrame(st.session_state['scanned_list'])
        
        # 編集可能なテーブルで最終確認
        edited_df = st.data_editor(df_export, num_rows="dynamic", use_container_width=True)
        
        st.write(f"現在 **{len(edited_df)}件** のデータが待機中です。")
        
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig') # UTF-8 BOM付き
        
        st.download_button(
            label="このリストをCSVでダウンロード",
            data=csv_data,
            file_name="ocr_scanned_data.csv",
            mime="text/csv",
            type="primary"
        )
        
        if st.button("リストをすべてクリア", type="secondary"):
            st.session_state['scanned_list'] = []
            st.rerun()
    else:
        st.info("現在追加されているデータはありません。")
