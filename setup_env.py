import os
import subprocess
import sys
import venv

def setup():
    # 1. 仮想環境のフォルダ名
    venv_dir = "venv"
    
    print(f"--- 1. 仮想環境 '{venv_dir}' を作成中... ---")
    if not os.path.exists(venv_dir):
        venv.create(venv_dir, with_pip=True)
        print("作成完了。")
    else:
        print("仮想環境は既に存在します。スキップします。")

    # 2. OSごとのPython実行パスの設定
    if os.name == "nt":  # Windows
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:  # Mac / Linux
        python_exe = os.path.join(venv_dir, "bin", "python")
        pip_exe = os.path.join(venv_dir, "bin", "pip")

    # 3. pip自体のアップグレード
    print("\n--- 2. pipを最新版に更新中... ---")
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

    # 4. 必要なライブラリのインストール
    # streamlit: UI
    # google-cloud-vision: OCR
    # pandas: データ処理
    # fpdf2: PDF作成（宛名用）
    # python-dotenv: 機密情報（APIキー等）の管理用
    libraries = [
        "streamlit",
        "google-cloud-vision",
        "pandas",
        "fpdf2",
        "python-dotenv"
    ]

    print(f"\n--- 3. ライブラリをインストール中... ---\n{', '.join(libraries)}")
    subprocess.run([pip_exe, "install"] + libraries)

    print("\n" + "="*40)
    print("環境構築が完了しました！")
    print("以下のコマンドでアプリを起動できます：")
    if os.name == "nt":
        print(f"{venv_dir}\\Scripts\\streamlit run main_app.py")
    else:
        print(f"source {venv_dir}/bin/activate && streamlit run app.py")
    print("="*40)

if __name__ == "__main__":
    setup()
