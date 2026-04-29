import os
import time
from google.genai.errors import APIError
from google.cloud import vision

# 1. 新しいパッケージのインポート
from google import genai
from dotenv import load_dotenv
from table_schema import MEMBER_APP_EXTR_PROMPT, MemberApplicationExtraction

load_dotenv(".env_app")  # set in ".env" file
VISION_API_KEY = os.getenv("VISION_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_VER = os.getenv("GEMINI_VER")
CSV_FILE = "ocr_scanned_data.csv"


# ==========================================
# API呼び出し関数の定義
# ==========================================
def extract_text_from_image(image_bytes: bytes) -> str:
    """Google Cloud Vision APIで画像から全テキストを抽出する（座標は無視）"""
    client = vision.ImageAnnotatorClient(client_options={"api_key": VISION_API_KEY})
    image = vision.Image(content=image_bytes)

    # 手書き・高密度テキストに強いDOCUMENT_TEXT_DETECTIONを使用
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")

    # 抽出されたテキスト全体を一つの文字列として返す
    return response.full_text_annotation.text


# 2. クライアントの初期化 (globalまたは関数内で保持)
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


def structure_text_with_gemini(raw_text: str, max_retries: int = 2) -> dict:
    """Gemini APIで生のテキストからJSONデータを抽出・構造化する（リトライ機能付き）"""
    if client is None:
        raise Exception("Gemini API Client is not initialized.")

    prompt = MEMBER_APP_EXTR_PROMPT.format(raw_text=raw_text)
    print(f"--- Prompt ---\n{prompt}")

    # Retry loop
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_VER,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": MemberApplicationExtraction,
                    "temperature": 0.0,
                },
            )
            # 4. 新しい SDK では .parsed で直接 Pydantic モデル（または dict）を取得可能
            # 元のコードに合わせて dict 形式で返したい場合は .model_dump() を使用します
            structured_data = response.parsed
            return structured_data.model_dump()

        except APIError as e:
            # Check if it's a 503 High Demand error
            if e.code == 503:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Waits 1s, then 2s, then 4s...
                    print(
                        f"Server busy (503). Retrying in {wait_time} seconds (Attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(wait_time)
                else:
                    raise Exception(
                        f"Gemini API failed after {max_retries} attempts due to high server demand: {e.message}"
                    )
            else:
                # If it's a different error (like 400 Bad Request or 401 Unauthorized), raise it immediately
                raise e
