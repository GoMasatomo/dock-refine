#!/usr/bin/env python3
"""
run_docking.py
このスクリプトは、タンパク質間ドッキングのためのパイプラインを実行するPythonプログラムです。
ZDOCK、HADDOCK、GROMACSなどのツールを使用して、以下の手順を自動化します。
1. ZDOCKを使用したドッキング計算の実行
2. クラスタリングによるPDBファイルのグループ化
3. インターフェイス残基の抽出
4. HADDOCK入力ファイルの生成
5. HADDOCKを使用したドッキング計算の実行
6. 代表構造の抽出とエネルギー解析

注意:
- ATOM, TER, END行以外が入力PDBファイルに含まれると予測が上手く行えない場合があります。
- スクリプトを実行する前に、必要な環境変数を設定してください。
- 入力ファイル（例: 7OPB_A.pdb, 7OPB_B.pdb）が適切に準備されていることを確認してください。

必要な環境変数:
- ZDOCK: ZDOCKの実行可能ファイルへのパス
- HADDOCK: HADDOCKの実行可能ファイルへのパス
- GROMACS: GROMACSの実行可能ファイルへのパス

関数:
- docking_pipeline(): ドッキングパイプライン全体を実行します。
- main(): 簡易的なドッキングとクラスタリングを実行します。

使用例:
$ python run_docking.py
"""

import os
import subprocess
import json
from dockmodules.run_zdock import ZDockRunner
from dockmodules.get_haddock_input import HaddockInputGenerator
from dockmodules.run_haddock import run_haddock
from dockmodules.run_clustering import cluster_pdb_files
from dockmodules.get_interface_residue import get_interface_residues
from dockmodules.haddock_analysis import HaddockAnalysis
import argparse
import random
from multiprocessing import Pool
import pandas as pd

def run_haddock_docking_for_cluster(cluster_id, cluster_df, receptor_pdb, ligand_pdb, interface_distance=8.0):
    #選択したcluster idの一番ZDockスコアの良かった構造を選択する
    members = cluster_df.loc[cluster_df['Cluster ID'] == cluster_id, 'Members'].values[0]
    first_member = str(members).split(',')[0].strip()
    pdb_file = f"complex.{first_member}.pdb"
    
    # インターフェイス残基の取得
    interface_residues = get_interface_residues(pdb_file, "A", "B", distance=interface_distance)

    # クラスター用ディレクトリの作成
    cluster_dir = f"Pos{cluster_id}"
    os.makedirs(cluster_dir, exist_ok=True)
    
    # 作成したディレクトリ内で操作を行う
    receptor_pdb_basename = os.path.basename(receptor_pdb)
    ligand_pdb_basename = os.path.basename(ligand_pdb)

    # PDBファイルをコピー
    subprocess.run(["cp", receptor_pdb, os.path.join(cluster_dir, receptor_pdb_basename)])
    subprocess.run(["cp", ligand_pdb, os.path.join(cluster_dir, ligand_pdb_basename)])

    # HADDOCK 入力ファイルの生成
    entries = [
        {
        "id": 1,
        "chain": "A",
        "active": list(interface_residues.get("A", [])),
        "structure": receptor_pdb_basename,
        "target": [2]
        },
        {
        "id": 2,
        "chain": "B",
        "active": list(interface_residues.get("B", [])),
        "structure": ligand_pdb_basename,
        "target": [1]
        }
    ]
    # リストをJSON文字列に変換
    entries_json = json.dumps(entries)
    generator = HaddockInputGenerator(entries_json)
    generator.main(output_dir=f"./{cluster_dir}")

    # HADDOCK の実行
    run_haddock(param_file=f"./{cluster_dir}/run.param", directory=f"./{cluster_dir}")

    # ./run1/structures/it1/water で HaddockAnalysis を実行
    analysis_dir = os.path.join(cluster_dir, "run1", "structures", "it1", "water")
    merged_df = None  # 初期化

    if os.path.exists(analysis_dir):
        analysis = HaddockAnalysis(analysis_dir)
        try:
            analysis.run_haddock_analysis()
            analysis.parse_cluster_score()
            merged_df = analysis.get_representative_structure()
            representative_structure_path = analysis.representative_structure_path
        except Exception as e:
            print(f"解析中にエラーが発生しました: {e}")
    else:
        print(f"ディレクトリ {analysis_dir} が存在しません。")

    return merged_df, representative_structure_path

def ensure_pdb_end_statement(pdb_file):
    """PDBファイルにENDステートメントがあるか確認し、なければ追加する"""
    with open(pdb_file, 'r+') as file:
        lines = file.readlines()
        if not lines[-1].strip() == "END":
            file.write("\nEND\n")

def docking_pipeline(receptor_pdb, ligand_pdb,output_dir="results", max_clusters=3, interface_distance=8.0, cluster_cutoff=0.45):
    # 環境変数の確認
    ZDOCK = os.environ.get("ZDOCK")
    HADDOCK = os.environ.get("HADDOCK")
    GROMACS = os.environ.get("GROMACS")

    if not ZDOCK or not HADDOCK or not GROMACS:
        raise EnvironmentError("必要な環境変数 (ZDOCK, HADDOCK, GROMACS) が設定されていません。")
    
    # receptor_pdb, ligand_pdb をフルパスに変換
    receptor_pdb = os.path.abspath(receptor_pdb)
    ligand_pdb = os.path.abspath(ligand_pdb)
    
    # 出力ディレクトリの作成
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)
    
    # dockingディレクトリを作成し、移動
    docking_dir = "docking"
    os.makedirs(docking_dir, exist_ok=True)
    os.chdir(docking_dir)
    
    # receptor_pdb, ligand_pdb を現在のディレクトリにコピー
    subprocess.run(["cp", receptor_pdb, "."])
    subprocess.run(["cp", ligand_pdb, "."])
    receptor_pdb = os.path.basename(receptor_pdb)
    ligand_pdb = os.path.basename(ligand_pdb)
    
    # PDBファイルにENDステートメントを追加
    ensure_pdb_end_statement(receptor_pdb)
    ensure_pdb_end_statement(ligand_pdb)

    # ZDOCK の実行
    zdock_runner = ZDockRunner()
    receptor_m_out = f"{os.path.splitext(receptor_pdb)[0]}_m.pdb"
    ligand_m_out = f"{os.path.splitext(ligand_pdb)[0]}_m.pdb"

    zdock_runner.mark_sur(receptor_pdb, receptor_m_out)
    zdock_runner.mark_sur(ligand_pdb, ligand_m_out)

    zdock_output = "zdock.out"
    zdock_runner.run_zdock(receptor_m_out, ligand_m_out, filename=zdock_output, num_predictions=2000, seed=random.randint(1, 100), is_dense_rot_samp=False, is_fix_receptor=False)
    
    num_preds = 100
    zdock_runner.create_pl(zdock_output, num_preds=num_preds)
    # クラスタリングの実行
    pdb_files = [f"complex.{i}.pdb" for i in range(1, num_preds + 1)]  # 最初の100個のPDBファイルを使用
    gmx_options = []
    cluster_df = cluster_pdb_files(pdb_files, gmx_options, cutoff_distance=cluster_cutoff, output_prefix="cluster")
    print("クラスタリング結果:", cluster_df)
    
    # クラスタリング結果から指定した数のクラスターIDを取得
    cluster_ids = cluster_df['Cluster ID'].unique().tolist()
    if len(cluster_ids) > max_clusters:
        cluster_ids = cluster_ids[:max_clusters]
    
    
    with Pool() as pool:
        results = pool.starmap(run_haddock_docking_for_cluster, [(cluster_id, cluster_df, receptor_pdb, ligand_pdb, interface_distance) for cluster_id in cluster_ids])

    # merged_df を結合し、#struc 列を更新
    combined_df = pd.concat([df.assign(**{"#struc": path}) for df, path in results], ignore_index=True)

    # score カラムを計算して追加
    combined_df["score"] = combined_df["Evdw"] + combined_df["Eelec"] + combined_df["Edesolv"]

    # #struc 列のファイルをコピー
    for path in combined_df["#struc"].unique():
        if os.path.exists(path):
            destination = os.path.join("copied_files", os.path.basename(path))
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            subprocess.run(["cp", path, destination])
            # 一個上の階層にコピー
            destination_upper = os.path.join("..", os.path.basename(path))
            subprocess.run(["cp", path, destination_upper])

    # combined_df を一つ上のディレクトリにファイルとして出力
    combined_df.to_csv("../combined_results.csv", index=False)

    print("クラスタリングとHADDOCK入力ファイルの生成が完了しました。")
    print("結合された結果:", combined_df)
    
def main():
    parser = argparse.ArgumentParser(description="タンパク質間ドッキングパイプラインを実行します。")
    parser.add_argument("receptor", help="レセプターPDBファイルのパス")
    parser.add_argument("ligand", help="リガンドPDBファイルのパス")
    parser.add_argument("-o", "--output", default="results", help="出力ディレクトリのパス (デフォルト: results)")
    parser.add_argument("-c", "--max-clusters", type=int, default=3, help="処理する最大クラスター数 (デフォルト: 3)")
    parser.add_argument("-d", "--interface-distance", type=float, default=8.0, help="インターフェイス残基の距離カットオフ (Å) (デフォルト: 8.0)")
    parser.add_argument("-t", "--cluster-cutoff", type=float, default=0.45, help="クラスタリングの距離カットオフ (nm) (デフォルト: 0.45)")
    args = parser.parse_args()

    docking_pipeline(args.receptor, args.ligand, args.output, args.max_clusters, args.interface_distance, args.cluster_cutoff)

if __name__ == "__main__":
    main()
