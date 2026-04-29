# 名簿管理ツール

- `main_app.py`: 名簿管理ツール
- `ocr_app.py`: 入力補助のための、外部APIを使用したOCRツール

## Setup
### 1. Python 3.14のインストール
まだPCに Python 3.14 が入っていない場合は、公式サイトからインストールしてください。

- Windows: Python.org から "Windows installer (64-bit)" をダウンロード。
- Mac: brew install python@3.14 または公式サイトから。

### 2. スクリプトの実行
ターミナル（Mac）またはコマンドプロンプト（Windows）を開き、Pythonをインストールした環境で以下を実行します

```
python setup_env.py
```

### 3. 印刷用Fontの配置
1. IPAのフォントダウンロードページ（文字情報技術促進協議会）にアクセスします。
https://moji.or.jp/ipafont/ipaex00401/
2. 「IPAexゴシック(Ver.xxxx)」 のZIPファイルをダウンロードして解凍します。
3. フォルダの中にある ipaexg.ttf というファイルを見つけます（これがフォントの本体です）。
4. 'main_app.py'と同じ場所に配置します。

### 4. OCRツールのためのAPIキーの取得
OCRにGoogle Vision APIを使用し、その結果の処理にGemini APIを使用します。
APIキーを取得し、`dot_env_app`の
`VISION_API_KEY`と`GEMINI_API_KEY`に設定してください。なお取得したAPIキーや記載したファイルは共有されないように注意し管理してください。

- Google Cloud Vision API: https://cloud.google.com/vision?hl=ja
- Gemini API: https://ai.google.dev/gemini-api/docs/api-key?hl=ja

### 5. アプリケーション

#### 準備

`dot_env_app`を編集し`.env_app`にファイル名を変更します。


#### 実行

実行ファイル
- 管理ツール`main_app.py`
- OCRツール`ocr_app.py`

```
# Windows
venv\Scripts\streamlit run {file}
# Mac
source venv/bin/activate && streamlit run {file}
```

#### 停止
ターミナル/コマンドプロンプトで`Ctrl + C` で停止

実行環境の停止は
```
 source venv/bin/deactivate
```



