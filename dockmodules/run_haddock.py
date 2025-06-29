#!/usr/bin/env python3
"""
このスクリプトは、HADDOCKドッキングソフトウェアの`run_haddock.py`スクリプトを実行するために使用されます。
スクリプトは以下の手順を実行します:
1. パラメータファイル（デフォルトは`run.param`）から`RUN_NUMBER`を読み取ります。
2. HADDOCKの`run_haddock.py`スクリプトを実行するコマンドを構築します。
3. 指定されたディレクトリおよび対応する実行ディレクトリでコマンドを実行します。
環境変数:
- HADDOCK: HADDOCKインストールディレクトリへのパス。この環境変数は設定されている必要があります。
関数:
- run_haddock(param_file="./run.param", directory="."):
    パラメータファイルから`RUN_NUMBER`を読み取り、指定されたディレクトリでHADDOCKスクリプトを実行します。
使用方法:
- このスクリプトはスタンドアロンプログラムとして直接実行できます。
"""
import subprocess
import os

# Set the environment variable for HADDOCK
HADDOCK = os.environ.get("HADDOCK")

def run_haddock(param_file="./run.param", directory="."):
    with open(param_file, "r") as file:
        for line in file:
            if line.startswith("RUN_NUMBER"):
                run_number = ''.join(filter(str.isdigit, line.split("=")[1]))
                break
    cmd = ["python", f"{HADDOCK}/haddock/run_haddock.py"]
    subprocess.run(cmd, cwd=directory)
    subprocess.run(cmd, cwd=f"{directory}/run{run_number}")
    

if __name__ == "__main__":
    run_haddock()
