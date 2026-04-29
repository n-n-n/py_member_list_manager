# py_member_list_manager

## Setup
### 1. Python 3.14のインストール
まだPCに Python 3.14 が入っていない場合は、公式サイトからインストールしてください。

- Windows: Python.org から "Windows installer (64-bit)" をダウンロード。
- Mac: brew install python@3.14 または公式サイトから。

### 2. スクリプトの実行
ターミナル（Mac）またはコマンドプロンプト（Windows）を開き、そのフォルダに移動して以下を打ちます。

```
python setup_env.py
```

### 3. 印刷用Fontの配置
1. IPAのフォントダウンロードページ（文字情報技術促進協議会）にアクセスします。
https://moji.or.jp/ipafont/ipaex00401/
2. 「IPAexゴシック(Ver.xxxx)」 のZIPファイルをダウンロードして解凍します。
3. フォルダの中にある ipaexg.ttf というファイルを見つけます（これがフォントの本体です）。
4. 'main_app.py'と同じ場所に配置します。

### アプリケーション

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


- 3. アプリケーションの停止
    ターミナル/コマンドプロンプトで`Ctrl + C` で停止

```
 source venv/bin/deactivate
```



