#!/usr/bin/env python3
"""
このスクリプトは、GROMACS分子動力学パッケージの`gmx cluster`コマンドを使用して
PDBファイルのクラスタリングを行う機能を提供します。複数のPDBファイルを1つのファイルに
結合し、クラスタリングプロセスを実行し、結果のログファイルをpandas DataFrameに解析して
分析します。

モジュール:
    - argparse: コマンドライン引数の解析用。
    - subprocess: 外部コマンドの実行用。
    - io.StringIO: メモリ内テキストストリームの処理用。
    - pandas: データ操作と分析用。
    - natsort: ファイル名の自然順ソート用。
    - re: 正規表現操作用。

関数:
    - run_clustering: PDBファイルを結合し、`gmx cluster`コマンドを実行してログファイルを生成します。
    - parse_cluster_log: クラスターログファイルを解析し、クラスタ情報を含むpandas DataFrameを返します。
    - cluster_pdb_files: クラスタリングとログ解析を組み合わせた高レベル関数。
    - main: スクリプトのエントリーポイントで、コマンドライン引数を処理し、クラスタリングプロセスを実行します。

使用方法:
    このスクリプトはコマンドラインから実行でき、PDBファイルをクラスタリングして結果を
    pandas DataFrameとして出力します。

例:
    python run_clustering.py complex.1.pdb complex.2.pdb --cutoff_distance 0.5 --output_prefix my_cluster

依存関係:
    - GROMACSがインストールされ、`gmx`コマンドとして利用可能である必要があります。
    - Pythonパッケージ: pandas, natsort。

注意:
    このスクリプトを実行する前に、環境で`gmx`コマンドが正しく設定されていることを確認してください。
"""
import os
import argparse
import subprocess
import pandas as pd
from natsort import natsorted
import numpy as np
import re

GROMACS = os.environ.get("GROMACS")

def run_clustering(pdb_files, gmx_options, cutoff_distance=0.45, output_prefix="cluster"):
    """
    複数のPDBファイルに対してgmx clusterコマンドを実行し、結合されたPDBファイルを生成します。

    引数:
        pdb_files (list): PDBファイルのパスのリスト
            例: ["complex.1.pdb", "complex.2.pdb"]
        gmx_options (list): gmx clusterコマンドに渡す追加オプション
                            例: ["-method", "linkage"]
        cutoff_distance (float): クラスタリングのカットオフ距離
                                 例: 0.45
        output_prefix (str): 出力ファイルの接頭辞
                             例: "cluster"

    戻り値:
        str: クラスターログファイルのパス。
        例: "cluster.log"
    """
    combined_file = f"{output_prefix}_combined.pdb"
    pdb_files = natsorted(pdb_files)
    represent_pdb = pdb_files[0]

    # 全てのPDBファイルを1つに結合する処理
    with open(combined_file, "w") as outfile:
        for identifier, pdb_file in enumerate(pdb_files):
            outfile.write(f"TITLE     AAA t=  {identifier + 1}\n")
            with open(pdb_file, "r") as infile:
                outfile.write(infile.read())
            outfile.write("ENDMDL\n")

    # gmx clusterコマンドを実行する
    command = [f"{GROMACS}", "cluster", "-f", combined_file, "-s", represent_pdb, "-cutoff", str(cutoff_distance)] + gmx_options
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input="3", text=True)

    if result.returncode != 0:
        print("Error running gmx cluster:")
        print(result.stderr)
        raise RuntimeError("gmx cluster command failed")

    return "cluster.log"

def parse_cluster_log(log_text="cluster.log"):
    """
    クラスターログファイルを解析し、クラスタ情報を含むDataFrameを返します。

    引数:
        log_text (str): ログファイルのパスまたはログ内容の文字列。
                        ".log"で終わる文字列が指定された場合、それはファイルパスとして扱われます。

    戻り値:
        pd.DataFrame: 解析されたクラスタ情報を含むDataFrame。以下の列を含みます:
        - "Cluster ID": クラスタのID
        - "# Structures": クラスタ内の構造数
        - "RMSD": クラスタのRMSD値
        - "Middle Structure": 中央構造のID
        - "Middle RMSD": 中央構造のRMSD値
        - "Members": メンバーIDのカンマ区切り文字列

    例外:
        FileNotFoundError: 指定されたログファイルパスが存在しない場合。
        ValueError: ログ内容が期待される形式でない場合。
    """
    if isinstance(log_text, str) and log_text.endswith(".log"):
        with open(log_text, "r", encoding="utf-8") as f:
            log_text = f.read()

    clusters = []
    current_cluster = None

    # ログファイルを1行ずつ解析する処理
    for line in log_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # クラスタ情報の行をマッチングする
        match = re.match(r"^\s*(\d+)\s*\|\s*(\d+)\s*([\d.]*)\s*\|\s*(\d+)\s*([\d.]*)\s*\|", line)
        if match:
            if current_cluster:
                clusters.append(current_cluster)

            cluster_id = int(match.group(1))
            num_structures = int(match.group(2))
            rmsd = float(match.group(3)) if match.group(3) else np.nan
            middle_id = int(match.group(4))
            middle_rmsd = float(match.group(5)) if match.group(5) else np.nan
            members = re.findall(r"\d+", line[match.end():])

            current_cluster = {
                "Cluster ID": cluster_id,
                "# Structures": num_structures,
                "RMSD": rmsd,
                "Middle Structure": middle_id,
                "Middle RMSD": middle_rmsd,
                "Members": members
            }
        elif current_cluster:
            members = re.findall(r"\d+", line)
            current_cluster["Members"].extend(members)

    if current_cluster:
        clusters.append(current_cluster)

    df = pd.DataFrame(clusters)
    df["Members"] = df["Members"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))

    return df

def cluster_pdb_files(pdb_files, gmx_options, cutoff_distance=0.45, output_prefix="cluster"):
    """
    gmx clusterを使用してPDBファイルをクラスタリングし、結果のログファイルをDataFrameで返します

    引数:
        pdb_files (list): PDBファイルのパスのリスト
        gmx_options (list): gmx clusterコマンドに渡す追加オプション
        cutoff_distance (float): クラスタリングのカットオフ距離
        output_prefix (str): 出力ファイルの接頭辞

    戻り値:
        pd.DataFrame: 解析されたクラスタ情報を含むDataFrame
    """
    log_file = run_clustering(pdb_files, gmx_options, cutoff_distance, output_prefix)
    df = parse_cluster_log(log_file)
    return df

def main():
    """
    コマンドライン引数を解析し、クラスタリングプロセスを実行するメイン関数。
    """
    parser = argparse.ArgumentParser(description="Run gmx cluster and convert the log to a pandas DataFrame.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("pdb_files", nargs="+", metavar="PDB_FILES",
                        help="Paths to the PDB files for clustering. (e.g., complex.1.pdb complex.2.pdb)")
    parser.add_argument("--gmx_options", type=str,
                        help="Additional options for gmx cluster (e.g., '--gmx_options \"-g test.log -method linkage\"')")
    parser.add_argument("--cutoff_distance", default=0.45, type=float,
                        help="Cutoff distance for gmx cluster (default: 0.45)")
    parser.add_argument("--output_prefix", default="cluster",
                        help="Prefix for output files (default: cluster)")

    args = parser.parse_args()
    gmx_options = args.gmx_options.split() if args.gmx_options else []

    df = cluster_pdb_files(args.pdb_files, gmx_options, args.cutoff_distance, args.output_prefix)
    print(df)

if __name__ == "__main__":
    main()