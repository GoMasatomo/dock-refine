#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
haddock_analysis.py

このスクリプトは、HADDOCKのドッキング計算結果を解析し、代表構造とそのエネルギー情報を抽出するためのツールです。
以下の手順で動作します:

1. 指定されたディレクトリに移動し、HADDOCK解析コマンドを実行します。
2. `cluster_haddock-score.txt_best4` ファイルを解析し、最もhaddockスコアが低いクラスターを選択します。
3. 選択したクラスターの `_ener` ファイルと `_Edesolv` ファイルを解析し、代表構造のファイル名とエネルギー情報を取得します。
4. 取得した情報を出力します。

使用例:
このスクリプトを実行するには、コマンドラインで以下のように入力します:
    python haddock_analysis.py /path/to/your/directory

例:
    python haddock_analysis.py ./Pos1/run1/structures/it1/water

依存関係:
- Python 3.x
- HADDOCK解析ツール

注意:
- 必要な入力ファイルが存在しない場合、スクリプトはエラーメッセージを出力して終了します。
- `_ener` ファイルと `_Edesolv` ファイルで構造名が一致しない場合、警告が表示されます。
"""

import os
import subprocess
import argparse
import pandas as pd


HADDOCKTOOLS = os.environ.get("HADDOCKTOOLS")

class HaddockAnalysis:
    """
    HaddockAnalysis クラス
    このクラスは、HADDOCK の解析を行うためのユーティリティを提供します。
    指定されたディレクトリ内で HADDOCK の解析コマンドを実行し、結果を解析して
    最適なクラスターを特定したり、エネルギー関連のデータを pandas.DataFrame として取得します。

    使用例:
    --------
    # HADDOCKTOOLS 環境変数を設定
    export HADDOCKTOOLS=/path/to/haddock/tools

    # HaddockAnalysis クラスをインスタンス化
    analysis = HaddockAnalysis("/path/to/haddock/output")

    # HADDOCK の解析を実行
    analysis.run_haddock_analysis()

    # 最適なクラスター名とそのスコアを取得
    best_cluster, best_score = analysis.parse_cluster_score()

    # 最適なクラスターのエネルギーデータを取得
    energy_data = analysis.parse_ener_and_edesolv_files(best_cluster)

    メソッド:
    ---------
    - __init__(directory):
        指定されたディレクトリを基にクラスを初期化します。
        - directory: HADDOCK の解析結果が保存されているディレクトリのパス。

    - run_haddock_analysis():
        指定したディレクトリに移動し、HADDOCK の解析コマンドを実行します。

    - parse_cluster_score(filename="cluster_haddock-score.txt_best4"):
        指定されたファイルを解析し、最もスコアが低いクラスター名とそのスコアを返します。
        - filename: クラスターのスコアが記録されたファイル名。

    - parse_ener_and_edesolv_files(cluster=None):
        指定されたクラスターの _ener と _Edesolv ファイルを解析し、それぞれの pandas.DataFrame を返します。
        - cluster: 解析対象のクラスター名。デフォルトでは self.best_cluster を使用します。
        
    - get_representative_structure():
        解析結果から代表構造（最初のインデックス）のデータフレームを返します。
    """
    def __init__(self, directory):
        self.directory = directory
        self.haddocktools = os.environ.get("HADDOCKTOOLS")
        self.best_cluster = None
        self.best_score = None
        self.representative_structure_path = None 

    def run_haddock_analysis(self):
        """
        指定したディレクトリに移動し、HADDOCKの解析コマンドを実行する。
        """
        command = [os.path.join(self.haddocktools, "ana_clusters.csh"), "-best", "4", "analysis/cluster.out"]
        result = subprocess.run(
            command,
            cwd=self.directory,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.PIPE
        )

    def parse_cluster_score(self, filename="cluster_haddock-score.txt_best4"):
        """
        cluster_haddock-score.txt_best4を読み込み、haddockスコアが最も低い（値が小さい）クラスター名を返す。
        """
        self.best_cluster = None
        self.best_score = float('inf')  # 最小値を探索（数値が小さい＝エネルギーが低い）
        filepath = os.path.join(self.directory, filename)
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    # ヘッダー行や空行はスキップ
                    if line.startswith("#") or not line:
                        continue
                    tokens = line.split()
                    if len(tokens) < 2:
                        continue
                    cluster_name = tokens[0]
                    try:
                        score = float(tokens[1])
                    except ValueError:
                        continue
                    if score < self.best_score:
                        self.best_score = score
                        self.best_cluster = cluster_name
        except FileNotFoundError:
            print(f"{filepath} が見つかりません。")
            exit(1)
        return self.best_cluster, self.best_score

    def parse_ener_and_edesolv_files(self, cluster=None):
        """
        指定されたクラスターの _ener と _Edesolv ファイルを解析し、それぞれの pandas.DataFrame を返す。
        デフォルトでは、self.best_cluster を使用する。
        """
        if cluster is None:
            cluster = self.best_cluster

        file_suffixes = {
            "ener": ["#struc", "Einter", "Enb", "Evdw+0.1Eelec", "Evdw", "Eelec", "Eair", "Ecdih", "Ecoup", "Esani", "Evean", "Edani"],
            "Edesolv": ["#struc", "Edesolv"]
        }

        def parse_file(cluster, suffix, columns):
            filename = os.path.join(self.directory, f"{cluster}_{suffix}")
            try:
                data = []
                with open(filename, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or not line:
                            continue
                        tokens = line.split()
                        data.append(tokens)
                df = pd.DataFrame(data, columns=columns)
                for col in columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
            except FileNotFoundError:
                print(f"{filename} が見つかりません。")
                return pd.DataFrame()

        ener_df = parse_file(cluster, "ener", file_suffixes["ener"])
        edesolv_df = parse_file(cluster, "Edesolv", file_suffixes["Edesolv"])

        if not ener_df.empty and not edesolv_df.empty:
            merged_df = pd.merge(ener_df, edesolv_df, on="#struc", how="inner")
            # 最初の構造のフルパスを保存
            if not merged_df.empty:
                self.representative_structure_path = os.path.join(self.directory, merged_df.iloc[0]["#struc"])
            return merged_df

        return pd.DataFrame()
        
    def get_representative_structure(self):
        """
        解析結果から代表構造（最初のインデックス）のデータフレームを返します。
        代表構造がない場合は空のデータフレームを返します。
        
        戻り値:
            pandas.DataFrame: 代表構造の情報を含む1行のデータフレーム
        """
        merged_df = self.parse_ener_and_edesolv_files()
        if merged_df.empty:
            return pd.DataFrame()
        return merged_df.iloc[[0]]
        

def parse_arguments():
    """
    コマンドライン引数を解析する関数。
    """
    parser = argparse.ArgumentParser(description="HADDOCKのドッキング計算結果から代表構造とエネルギーを抽出するスクリプト")
    parser.add_argument("directory", help="解析対象のディレクトリパス")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # HaddockAnalysis クラスのインスタンスを作成
    analysis = HaddockAnalysis(args.directory)

    # 指定ディレクトリに移動し、解析コマンドを実行
    analysis.run_haddock_analysis()

    # cluster_haddock-score.txt_best4 をパースして、最もスコアが低いクラスターを選択
    best_cluster, best_score = analysis.parse_cluster_score()
    if best_cluster is None:
        print("有効なクラスターが見つかりませんでした。")
        exit(1)
    print(f"最もhaddockスコアが低いクラスター: {best_cluster} (スコア: {best_score})")

    # 選択したクラスターの _ener, _Edesolv ファイルから、最初の構造の情報を取得
    #merged_df = analysis.parse_ener_and_edesolv_files()
    merged_df = analysis.get_representative_structure()
    if merged_df.empty:
        print("必要なファイルが見つからないか、データが空です。")
        exit(1)

    # 代表構造とエネルギー情報を出力
    print("\n代表構造とエネルギー情報:")
    print("構造ファイル名:", merged_df.iloc[0]["#struc"])
    print("エネルギー情報:", merged_df.iloc[0].to_dict())
    print("代表構造のフルパス:", analysis.representative_structure_path)


if __name__ == "__main__":
    main()
