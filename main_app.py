import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
import os
from datetime import datetime
from dotenv import load_dotenv

# --- 1. 環境変数の読み込み ---
load_dotenv()
APP_TITLE = os.getenv("APP_TITLE", "コミュニティ名簿管理")
APP_FONT = os.getenv("APP_FONT", "sans-serif")
PDF_FONT_PATH = os.getenv("PDF_FONT_PATH", "ipaexg.ttf")

# --- 2. ページ設定とカスタムフォント適用 ---
st.set_page_config(page_title=APP_TITLE, layout="wide")

st.markdown(f"""
    <style>
        html, body, [class*="st-"] {{
            font-family: {APP_FONT} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- 3. データベース初期化 ---
def init_db():
    conn = sqlite3.connect('community.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, zip_code TEXT, address TEXT, tel TEXT, 
                  fee INTEGER, comment TEXT)''')
    conn.commit()
    return conn

# --- ★ 高機能検索クエリ作成関数 ★ ---
def build_search_query(base_query, search_term):
    if not search_term:
        return base_query, ()
    
    # 全角スペースを半角スペースに変換し、空白で分割 (AND検索対応)
    words = search_term.replace('　', ' ').split()
    
    where_clauses = []
    params = []
    
    for word in words:
        # ユーザーが入力した '*' を SQLの '%' に、'?' を '_' に変換
        if '*' in word or '?' in word:
            sql_word = word.replace('*', '%').replace('?', '_')
        else:
            # ワイルドカード指定がない場合は、自動で前後を部分一致にする
            sql_word = f"%{word}%"
        
        where_clauses.append("(name LIKE ? OR address LIKE ?)")
        params.extend([sql_word, sql_word])
    
    # WHERE句を AND でつなぐ
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
        
    return base_query, tuple(params)

# --- 4. PDF作成クラス ---
class HagakiPDF(FPDF):
    def setup_font(self):
        if os.path.exists(PDF_FONT_PATH):
            self.add_font('Japanese', '', PDF_FONT_PATH)
            self.set_font('Japanese', '', 12)
        else:
            self.set_font('helvetica', '', 12)

def create_address_pdf(selected_members):
    pdf = HagakiPDF(orientation='P', unit='mm', format=(100, 148))
    pdf.setup_font()
    for _, m in selected_members.iterrows():
        pdf.add_page()
        pdf.set_font('Japanese', '', 10)
        pdf.text(10, 20, f"〒 {m['zip_code']}")
        pdf.text(10, 30, f"{m['address']}")
        pdf.set_font('Japanese', '', 16)
        pdf.text(30, 70, f"{m['name']}  様")
    return pdf.output()

# --- 5. メインUI ---
conn = init_db()

st.title(f"📇 {APP_TITLE}")

tabs = st.tabs(["名簿一覧・詳細編集", "CSV / データ一括管理", "宛名PDF出力"])

# === Tab 1: 名簿一覧・詳細編集 ===
with tabs[0]:
    col_list, col_edit = st.columns([3, 2])
    
    with col_list:
        st.header("名簿一覧")
        search_term = st.text_input("検索（「山田*」で前方一致、スペースでAND検索）", key="tab1_search")
        
        # 検索クエリの構築と実行
        base_query = "SELECT id, name, zip_code, address, tel, fee, comment FROM members"
        query, params = build_search_query(base_query, search_term)
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            st.dataframe(df.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("データがありません。")

    with col_edit:
        st.header("個別編集パネル")
        NEW_ENTRY_MODE = "＋ 新規登録（新しいメンバーを追加）"
        member_names = [NEW_ENTRY_MODE] + (df['name'].tolist() if not df.empty else [])
            
        selected_name = st.selectbox("操作対象を選択", member_names)
        is_new_entry = (selected_name == NEW_ENTRY_MODE)
        
        if is_new_entry:
            m_data = {'name': '', 'zip_code': '', 'address': '', 'tel': '', 'fee': 0, 'comment': ''}
            m_id = None
        else:
            m_data = df[df['name'] == selected_name].iloc[0]
            m_id = int(m_data['id'])
        
        with st.form("edit_member_form"):
            e_name = st.text_input("氏名", value=m_data['name'])
            e_zip = st.text_input("郵便番号", value=m_data['zip_code'])
            e_addr = st.text_input("住所", value=m_data['address'])
            e_tel = st.text_input("電話番号", value=m_data['tel'])
            e_fee = st.number_input("会費", value=int(m_data['fee']))
            e_comment = st.text_area("全コメント（編集可能）", value=m_data['comment'], height=100)
            
            st.markdown("---")
            log_author = st.text_input("記入者名（追記用）")
            new_log_text = st.text_area("追記内容")
            
            col_save, col_del = st.columns(2)
            with col_save:
                save_btn = st.form_submit_button("登録 / 保存")
            with col_del:
                if not is_new_entry:
                    delete_check = st.checkbox("完全に削除する")
                    delete_btn = st.form_submit_button("実行（削除）")
                else:
                    delete_check, delete_btn = False, False

        # 保存処理
        if save_btn and e_name:
            final_comment = e_comment
            if log_author and new_log_text:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                final_comment += f"\n[{ts} {log_author}] {new_log_text}"
            
            c = conn.cursor()
            if is_new_entry:
                c.execute("INSERT INTO members (name, zip_code, address, tel, fee, comment) VALUES (?,?,?,?,?,?)", 
                          (e_name, e_zip, e_addr, e_tel, e_fee, final_comment))
            else:
                c.execute("UPDATE members SET name=?, zip_code=?, address=?, tel=?, fee=?, comment=? WHERE id=?", 
                          (e_name, e_zip, e_addr, e_tel, e_fee, final_comment, m_id))
            conn.commit()
            st.success("保存しました。")
            st.rerun()

        # 個別削除処理
        if delete_btn and delete_check:
            c = conn.cursor()
            c.execute("DELETE FROM members WHERE id=?", (m_id,))
            conn.commit()
            st.warning("削除しました。")
            st.rerun()

# === Tab 2: CSV / データ一括管理 ===
with tabs[1]:
    st.header("データの一括処理")
    col_in, col_out = st.columns(2)
    
    with col_in:
        st.subheader("📥 CSVインポート（追加）")
        uploaded_csv = st.file_uploader("CSVファイルをアップロード", type=["csv"])
        if uploaded_csv:
            import_df = pd.read_csv(uploaded_csv)
            st.dataframe(import_df.head(3))
            if st.button("このデータをDBに追加する"):
                try:
                    import_df.to_sql('members', conn, if_exists='append', index=False)
                    st.success(f"{len(import_df)} 件のデータを追加しました！")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    with col_out:
        st.subheader("📤 CSVエクスポート（バックアップ）")
        all_df = pd.read_sql_query("SELECT name, zip_code, address, tel, fee, comment FROM members", conn)
        if not all_df.empty:
            csv_data = all_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("全データを出力 (CSV)", csv_data, f"community_members_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            
    st.markdown("---")
    
    st.subheader("🗑️ レコードの検索と選択削除")
    st.write("検索で絞り込み、削除したいメンバーにチェックを入れて実行してください。")
    
    del_search_term = st.text_input("削除対象を検索（「*」やスペース区切り対応）", key="del_search")
    
    # 検索クエリの構築と実行
    del_base_query = "SELECT id, name, zip_code, address, tel FROM members"
    del_query, del_params = build_search_query(del_base_query, del_search_term)
    del_df = pd.read_sql_query(del_query, conn, params=del_params)
    
    if not del_df.empty:
        del_df.insert(0, '削除対象', False)
        edit_del_df = st.data_editor(del_df, hide_index=True, use_container_width=True, disabled=["id","name","zip_code","address","tel"])
        targets_to_delete = edit_del_df[edit_del_df['削除対象'] == True]['id'].tolist()
        
        if len(targets_to_delete) > 0:
            if st.button(f"選択した {len(targets_to_delete)} 件を完全に削除する", type="primary"):
                c = conn.cursor()
                c.executemany("DELETE FROM members WHERE id=?", [(tid,) for tid in targets_to_delete])
                conn.commit()
                st.success(f"{len(targets_to_delete)}件のデータを削除しました。")
                st.rerun()
    else:
        st.info("該当するデータがありません。")

# === Tab 3: 宛名出力 ===
with tabs[2]:
    st.header("葉書宛名PDF出力")
    st.write("検索で対象を絞り込み、印刷したいメンバーを選択してください。")
    
    pdf_search_term = st.text_input("宛名対象を検索（「*」やスペース区切り対応）", key="pdf_search")
    
    # 検索クエリの構築と実行
    pdf_base_query = "SELECT id, name, zip_code, address FROM members"
    pdf_query, pdf_params = build_search_query(pdf_base_query, pdf_search_term)
    pdf_df = pd.read_sql_query(pdf_query, conn, params=pdf_params)
    
    if not pdf_df.empty:
        pdf_df.insert(0, '印刷対象', False)
        select_editor = st.data_editor(pdf_df, hide_index=True, use_container_width=True, disabled=["id","name","zip_code","address"])
        selected_members = select_editor[select_editor['印刷対象'] == True]
        
        if st.button(f"{len(selected_members)}件の宛名PDFを作成"):
            pdf_data = create_address_pdf(selected_members)
            st.download_button("📥 PDFをダウンロード", bytes(pdf_data), f"address.pdf", "application/pdf")
    else:
        st.info("該当するデータがありません。")
