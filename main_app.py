import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
import os
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

from table_schema import MemberApplicationDB

# --- 2. 環境変数の読み込みと設定 ---
load_dotenv(".env_app")
APP_TITLE = os.getenv("APP_TITLE", "霊園申込・名簿管理システム")
APP_FONT = os.getenv("APP_FONT", "sans-serif")
PDF_FONT_PATH = os.getenv("PDF_FONT_PATH", "ipaexg.ttf")

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.markdown(
    f"""
    <style>
        html, body, [class*="st-"] {{ font-family: {APP_FONT} !important; }}
    </style>
""",
    unsafe_allow_html=True,
)


# --- 3. データベース初期化 (Pydanticから自動生成) ---
def init_db():
    conn = sqlite3.connect("cemetery_management.db", check_same_thread=False)
    c = conn.cursor()

    # スキーマからカラム定義を動的に作成
    col_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
    for field_name, field_info in MemberApplicationDB.model_fields.items():
        # int型が含まれていればINTEGER、それ以外はTEXTとする
        if "int" in str(field_info.annotation).lower():
            col_defs.append(f"{field_name} INTEGER")
        else:
            col_defs.append(f"{field_name} TEXT")

    query = f"CREATE TABLE IF NOT EXISTS members ({', '.join(col_defs)})"
    c.execute(query)
    conn.commit()
    return conn


# --- 4. 検索クエリ作成 ---
def build_search_query(base_query, search_term):
    if not search_term:
        return base_query, ()

    words = search_term.replace("　", " ").split()
    where_clauses = []
    params = []

    for word in words:
        if "*" in word or "?" in word:
            sql_word = word.replace("*", "%").replace("?", "_")
        else:
            sql_word = f"%{word}%"
        # 氏名、ふりがな、住所を検索対象にする
        where_clauses.append(
            "(applicant_name LIKE ? OR applicant_furigana LIKE ? OR address LIKE ?)"
        )
        params.extend([sql_word, sql_word, sql_word])

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    return base_query, tuple(params)


# --- 5. PDF作成クラス (宛名のキーを修正) ---
class HagakiPDF(FPDF):
    def setup_font(self):
        if os.path.exists(PDF_FONT_PATH):
            self.add_font("Japanese", "", PDF_FONT_PATH)
            self.set_font("Japanese", "", 12)
        else:
            self.set_font("helvetica", "", 12)


def create_address_pdf(selected_members):
    pdf = HagakiPDF(orientation="P", unit="mm", format=(100, 148))
    pdf.setup_font()
    for _, m in selected_members.iterrows():
        pdf.add_page()
        pdf.set_font("Japanese", "", 10)
        pdf.text(10, 20, f"〒 {m['zip_code']}")
        pdf.text(10, 30, f"{m['address']}")
        pdf.set_font("Japanese", "", 16)
        # applicant_name に変更
        pdf.text(30, 70, f"{m['applicant_name']}  様")
    return pdf.output()


# --- 6. メインUI ---
conn = init_db()
st.title(f"📇 {APP_TITLE}")
tabs = st.tabs(["名簿一覧・詳細編集", "CSV / データ一括管理", "宛名PDF出力"])

# === Tab 1: 名簿一覧・詳細編集 ===
with tabs[0]:
    col_list, col_edit = st.columns([3, 2])

    with col_list:
        st.header("申込データ一覧")
        search_term = st.text_input("検索（名前・ふりがな・住所）", key="tab1_search")

        base_query = "SELECT * FROM members"
        query, params = build_search_query(base_query, search_term)
        df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:
            # IDを隠して表示
            st.dataframe(df.drop(columns=["id"]), width="stretch", hide_index=True)
        else:
            st.info("データがありません。")

    with col_edit:
        st.header("個別編集パネル")
        NEW_ENTRY_MODE = "＋ 新規登録（新しい申込を追加）"
        member_names = [NEW_ENTRY_MODE] + (
            df["applicant_name"].tolist() if not df.empty else []
        )

        selected_name = st.selectbox("操作対象を選択", member_names)
        is_new_entry = selected_name == NEW_ENTRY_MODE

        if is_new_entry:
            m_id = None
        else:
            # 選択された行のデータを取得
            m_data = df[df["applicant_name"] == selected_name].iloc[0]
            m_id = int(m_data["id"])

        with st.form("edit_member_form"):
            # Pydanticスキーマからフォーム項目を自動生成 (2カラムレイアウト)
            form_cols = st.columns(2)
            form_data = {}

            for i, (f_name, f_info) in enumerate(
                MemberApplicationDB.model_fields.items()
            ):
                # 左右に交互に配置
                target_col = form_cols[i % 2]
                desc = f_info.description or f_name
                is_int = "int" in str(f_info.annotation).lower()

                # 初期値の取得
                if is_new_entry:
                    default_val = 0 if is_int else ""
                else:
                    default_val = m_data[f_name]
                    if pd.isna(default_val):  # DBのNULL対策
                        default_val = 0 if is_int else ""

                with target_col:
                    if f_name == "remarks":
                        form_data[f_name] = st.text_area(
                            desc, value=str(default_val), height=100
                        )
                    elif is_int:
                        form_data[f_name] = st.number_input(
                            desc, value=int(default_val)
                        )
                    else:
                        form_data[f_name] = st.text_input(desc, value=str(default_val))

            st.markdown("---")
            log_author = st.text_input("記入者名（ログ追記用）")
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

        # --- 保存・更新処理 (SQL自動生成) ---
        if save_btn and form_data.get("applicant_name"):
            # ログの追記処理
            if log_author and new_log_text:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                form_data["remarks"] += f"\n[{ts} {log_author}] {new_log_text}"

            c = conn.cursor()
            keys = list(form_data.keys())
            values = list(form_data.values())

            if is_new_entry:
                placeholders = ", ".join(["?"] * len(keys))
                q = f"INSERT INTO members ({', '.join(keys)}) VALUES ({placeholders})"
                c.execute(q, values)
            else:
                set_clause = ", ".join([f"{k}=?" for k in keys])
                q = f"UPDATE members SET {set_clause} WHERE id=?"
                c.execute(q, values + [m_id])

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
                    import_df.to_sql("members", conn, if_exists="append", index=False)
                    st.success(f"{len(import_df)} 件のデータを追加しました！")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    with col_out:
        st.subheader("📤 CSVエクスポート（バックアップ）")
        all_df = pd.read_sql_query("SELECT * FROM members", conn).drop(columns=["id"])
        if not all_df.empty:
            csv_data = all_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "全データを出力 (CSV)",
                csv_data,
                f"cemetery_data_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
            )

    st.markdown("---")
    st.subheader("🗑️ レコードの検索と選択削除")

    del_search_term = st.text_input("削除対象を検索", key="del_search")
    del_base_query = (
        "SELECT id, applicant_name, zip_code, address, phone_home FROM members"
    )
    del_query, del_params = build_search_query(del_base_query, del_search_term)
    del_df = pd.read_sql_query(del_query, conn, params=del_params)

    if not del_df.empty:
        del_df.insert(0, "削除対象", False)
        # 削除用テーブルの表示列を制限（見やすくするため）
        disabled_cols = ["id", "applicant_name", "zip_code", "address", "phone_home"]
        edit_del_df = st.data_editor(
            del_df, hide_index=True, use_container_width=True, disabled=disabled_cols
        )
        targets_to_delete = edit_del_df[edit_del_df["削除対象"] == True]["id"].tolist()

        if len(targets_to_delete) > 0:
            if st.button(
                f"選択した {len(targets_to_delete)} 件を完全に削除する", type="primary"
            ):
                c = conn.cursor()
                c.executemany(
                    "DELETE FROM members WHERE id=?",
                    [(tid,) for tid in targets_to_delete],
                )
                conn.commit()
                st.success(f"{len(targets_to_delete)}件のデータを削除しました。")
                st.rerun()
    else:
        st.info("該当するデータがありません。")

# === Tab 3: 宛名出力 ===
with tabs[2]:
    st.header("葉書宛名PDF出力")
    pdf_search_term = st.text_input("宛名対象を検索", key="pdf_search")

    pdf_base_query = "SELECT id, applicant_name, zip_code, address FROM members"
    pdf_query, pdf_params = build_search_query(pdf_base_query, pdf_search_term)
    pdf_df = pd.read_sql_query(pdf_query, conn, params=pdf_params)

    if not pdf_df.empty:
        pdf_df.insert(0, "印刷対象", False)
        disabled_cols = ["id", "applicant_name", "zip_code", "address"]
        select_editor = st.data_editor(
            pdf_df, hide_index=True, use_container_width=True, disabled=disabled_cols
        )
        selected_members = select_editor[select_editor["印刷対象"] == True]

        if st.button(f"{len(selected_members)}件の宛名PDFを作成"):
            pdf_data = create_address_pdf(selected_members)
            st.download_button(
                "📥 PDFをダウンロード",
                bytes(pdf_data),
                f"address.pdf",
                "application/pdf",
            )
    else:
        st.info("該当するデータがありません。")
