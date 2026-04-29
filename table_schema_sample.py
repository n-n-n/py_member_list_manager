from pydantic import BaseModel, Field
from typing import Optional


# ==========================================
# 1. データスキーマの定義 (Pydantic)
# ==========================================
class MemberApplicationExtraction(BaseModel):
    reception_date: Optional[str] = Field(description="受付日(例: 令和5年10月1日)")
    applicant_name: Optional[str] = Field(description="使用者氏名")
    applicant_furigana: Optional[str] = Field(description="使用者氏名のふりがな")
    zip_code: Optional[str] = Field(description="現住所の郵便番号(ハイフンあり)")
    address: Optional[str] = Field(description="現住所")
    phone_home: Optional[str] = Field(description="ご自宅の電話番号")
    phone_mobile: Optional[str] = Field(description="携帯番号")
    management_fee: Optional[int] = Field(description="管理料の金額")
    remittance_amount: Optional[int] = Field(description="送金金額")
    remittance_limit_date: Optional[str] = Field(
        description="送金期限日(例: 令和5年10月1日)"
    )
    referrer: Optional[str] = Field(description="紹介者")
    contact_name: Optional[str] = Field(description="連絡先の氏名")
    contact_zip_code: Optional[str] = Field(
        description="連絡先の郵便番号"
    )  # ※説明文を修正
    contact_phone: Optional[str] = Field(description="連絡先の電話番号")
    contact_address: Optional[str] = Field(description="連絡先の住所")


class MemberApplicationDB(MemberApplicationExtraction):
    # 以前の機能（対応ログ）を維持するための追加フィールド
    remarks: Optional[str] = Field(default="", description="[ref]備考・対応ログ")
    # id: Optional[str] = Field(default="", description="[ref]備考・対応ログ")


MEMBER_APP_EXTR_PROMPT = """
    あなたはOCRで読み取られた申込書のテキストを構造化データに変換する専門家です。
    以下の【生のテキストデータ】から情報を抽出し、指定されたJSONスキーマに従って出力してください。

    【制約事項】
    - テキストに存在しない項目は null としてください。
    - 金額欄に「|」や「,」が含まれている場合、それらを除去して純粋な整数（数値）にしてください。
      （例: "1|2|0|0|0|0" -> 120000）
    - 住所の正規化や和暦の西暦変換は行わず、読み取れた通りに出力してください。推論は不要です。
    【生のテキストデータ】
    {raw_text}
"""
