#!/usr/bin/env python3
"""
このスクリプトは、指定されたPDBファイルからタンパク質構造内の2つのチェーン間のインターフェイス残基を特定します。
インターフェイス残基は、2つのチェーン内の残基の原子間の距離に基づいて決定されます。
スクリプトはBiopythonライブラリを使用してPDBファイルを解析し、原子間の距離を計算します。
各チェーンのインターフェイス残基をソートされたリスト形式で出力します。

使用方法:
    以下の引数を指定してコマンドラインからスクリプトを実行します:
    - pdb_file: PDBファイルのパス
    - chain1: 最初のチェーンID (例: 'A')
    - chain2: 2番目のチェーンID (例: 'B')
    - --distance: (オプション) インターフェイスとみなす距離の閾値 (Å) (デフォルトは8.0Å)

例:
    python get_interface_residue.py example.pdb A B --distance 6.0

依存関係:
    - Biopython

関数:
    - get_interface_residues: 距離の閾値に基づいて2つのチェーン間のインターフェイス残基を特定します。
"""
import warnings
from Bio import BiopythonWarning
from Bio.PDB import *
from Bio.PDB.PDBParser import PDBParser
import argparse

# Biopythonの警告を無視
warnings.simplefilter("ignore", BiopythonWarning)

def get_interface_residues(pdb_file, chain1, chain2, distance=8.0):
    """
    2つのチェーン間のインターフェイス残基を特定する関数。

    この関数は、指定されたPDBファイル内の2つのチェーン間で、指定された距離以内にある
    インターフェイス残基を特定します。結果は、各チェーンのインターフェイス残基のリストとして
    辞書形式で返されます。

    引数:
        pdb_file (str): PDBファイルのパス (例: 'protein.pdb')。
        chain1 (str): 最初のチェーンID (例: 'A')。
        chain2 (str): 2番目のチェーンID (例: 'B')。
        distance (float, オプション): インターフェイスとみなす距離 (Å)。デフォルトは8.0Å。

    戻り値:
        dict: 各チェーンのインターフェイス残基リストを含む辞書。
              形式: {chain1: [残基番号リスト], chain2: [残基番号リスト]}。

    使用例:
        >>> interface_residues = get_interface_residues('protein.pdb', 'A', 'B', distance=8.0)
        >>> print(interface_residues)
        {'A': [10, 15, 20], 'B': [5, 12, 18]}

    注意:
        - この関数はBiopythonライブラリを使用してPDBファイルを解析し、原子間の距離を計算します。
        - 残基は、1つの残基内の任意の原子が他の残基内の任意の原子と指定された距離以内にある場合、
          インターフェイスの一部と見なされます。
        - PDBファイルとチェーンIDが有効であることを確認してください。
    """
    # PDBファイルの読み込み
    parser = PDBParser(PERMISSIVE=True)
    structure = parser.get_structure("protein", pdb_file)
    
    # 指定したチェーンを取得
    model = structure[0]
    chain_a = model[chain1]
    chain_b = model[chain2]
    
    # 各チェーンの残基と原子を取得
    residues_a = list(chain_a.get_residues())
    residues_b = list(chain_b.get_residues())
    
    # インターフェイス残基を格納するセット
    interface_a = set()
    interface_b = set()
    
    # 各残基の原子間距離を計算
    for res_a in residues_a:
        for res_b in residues_b:
            # 残基内の全ての原子間の距離をチェック
            for atom_a in res_a:
                for atom_b in res_b:
                    if atom_a - atom_b <= distance:
                        interface_a.add(res_a)
                        interface_b.add(res_b)
                        break  # 1つでも近い原子があれば十分
                else:
                    continue  # 内側のループがbreakされなかった場合のみ実行
                break  # 外側のループをbreak
    # インターフェイス残基をA:1,2,3の形式で取得
    interface_dict = {
        chain1: [res.get_id()[1] for res in sorted(interface_a, key=lambda x: x.get_id()[1])],
        chain2: [res.get_id()[1] for res in sorted(interface_b, key=lambda x: x.get_id()[1])]
    }
    return interface_dict


if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="2つのチェーン間のインターフェイス残基を取得するスクリプト")
    parser.add_argument("pdb_file", type=str, help="PDBファイルのパス")
    parser.add_argument("chain1", type=str, help="最初のチェーンID (例: 'A')")
    parser.add_argument("chain2", type=str, help="2番目のチェーンID (例: 'B')")
    parser.add_argument("--distance", type=float, default=8.0, help="インターフェイスとみなす距離 (Å) (デフォルト: 8.0)")
    
    args = parser.parse_args()
    
    # インターフェイス残基を取得
    interface_residues = get_interface_residues(args.pdb_file, args.chain1, args.chain2, args.distance)
    print(interface_residues)
    # 結果を表示
    print(f"Chain {args.chain1} interface residues: {interface_residues[args.chain1]}")
    print(f"Chain {args.chain2} interface residues: {interface_residues[args.chain2]}")
