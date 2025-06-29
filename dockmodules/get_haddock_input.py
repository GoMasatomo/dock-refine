#!/usr/bin/env python3
"""
このスクリプトは、分子ドッキングソフトウェアHADDOCKの入力ファイルを生成し、haddock-restraintsツールを実行します。
スクリプトは以下のタスクを実行します：
1. 分子ドッキングパラメータを記述したJSON形式の入力エントリを解析します。
2. 入力エントリに基づいてJSON構成ファイルを生成します。
3. haddock-restraintsツールを実行して拘束ファイルを生成します。
4. HADDOCKの実行に必要な`run.param`ファイルを作成します。
クラス:
    HaddockInputGenerator: 入力ファイルの生成とhaddock-restraintsの実行を処理します。
関数:
    parse_arguments(): コマンドライン引数を解析してJSON形式の入力エントリを取得します。
使用方法:
    `--entries`引数にドッキングパラメータのJSON文字列を含めてスクリプトを実行します。
    例:
        python get_haddock_input.py --entries '[{"id": 1, "chain": "A", "active": [29, 30, 31], "structure": "protein1.pdb", "target": [2]}, {"id": 2, "chain": "B", "active": [8, 11, 12], "structure": "protein2.pdb", "target": [1]}]'
"""
import json
import subprocess
import argparse
import os

HADDOCK = os.environ.get("HADDOCK")
HADDOCK_RESTRAINTS = os.environ.get("HADDOCK_RESTRAINTS")

class HaddockInputGenerator:
    """
    HADDOCK入力を生成および処理するためのクラス。

    Attributes:
        entries (list): 入力データのエントリを格納するリスト。
        data (list): 処理されたデータを格納するリスト。

    Methods:
        __init__(entries):
            クラスのインスタンスを初期化します。

        generate_json_output(output_file):
            処理されたデータをJSON形式で指定されたファイルに出力します。

        create_data_entry(id, chain, active, structure, target, passive=None, passive_from_active=True, filter_buried=True):
            データエントリを作成します。

        run_haddock_restraints(config_file, output_file):
            HADDOCKの拘束条件を生成する外部コマンドを実行します。

        generate_run_param_file(output_file="./run.param", ambig_tbl="./restraints.tbl", haddock_dir=f"{haddock_root}/haddock2.4-2024-03/", project_dir=".", run_number="1"):
            HADDOCKの実行に必要なパラメータファイルを生成します。

        process_entries():
            入力データを処理し、データエントリを作成します。

        main(output_dir="."):
            全体の処理フローを実行します。

    使用例:
        entries = '[{"id": 1, "chain": "A", "active": [29, 30, 31], "structure": "protein1.pdb", "target": [2]}, {"id": 2, "chain": "B", "active": [8, 11, 12], "structure": "protein2.pdb", "target": [1]}]'
        generator = HaddockInputGenerator(entries)
        generator.main()
    """
    def __init__(self, entries):
        self.entries = json.loads(entries)
        self.data = []

    def generate_json_output(self, output_file):
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def create_data_entry(self, id, chain, active, structure, target, passive=None, passive_from_active=True, filter_buried=True):
        if passive is None:
            passive = []
        return {
            "id": id,
            "chain": chain,
            "active": active,
            "passive": passive,
            "structure": structure,
            "target": target,
            "passive_from_active": passive_from_active,
            "filter_buried": filter_buried
        }

    def run_haddock_restraints(self, config_file, output_file):
        command = [f"{HADDOCK_RESTRAINTS}/haddock-restraints", "tbl", config_file]
        try:
            with open(output_file, 'w') as f:
                subprocess.run(command, stdout=f, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def generate_run_param_file(self, output_file="./run.param", ambig_tbl="./restraints.tbl", haddock_dir=f"{HADDOCK}/haddock2.4-2024-03/", project_dir=".", run_number="1"):
        content = f"""AMBIG_TBL={ambig_tbl}
HADDOCK_DIR={haddock_dir}
RUN_NUMBER={run_number}
N_COMP=2
PROJECT_DIR={project_dir}
"""

        for i, entry in enumerate(self.entries, start=1):
                content += f"PDB_FILE{i}={entry['structure']}\n"
                content += f"PROT_SEGID_{i}={entry['chain']}\n"

        with open(output_file, 'w') as f:
            f.write(content)

    def process_entries(self):
        self.data = [
            self.create_data_entry(entry['id'], entry['chain'], entry['active'], entry['structure'], entry['target'], entry.get(
                'passive', []), entry.get('passive_from_active', True), entry.get('filter_buried', True))
            for entry in self.entries
        ]

    def main(self, output_dir="."):
        self.process_entries()
        config_file = os.path.join(output_dir, "output.json")
        self.generate_json_output(config_file)

        restraints_output_file = os.path.join(output_dir, "restraints.tbl")
        self.run_haddock_restraints(config_file, restraints_output_file)

        run_param_file = os.path.join(output_dir, "run.param")
        ambig_tbl = f"./restraints.tbl"
        haddock_dir = f"{HADDOCK}/"
        project_dir = "."
        run_number = 1
        self.generate_run_param_file(
            run_param_file, ambig_tbl, haddock_dir, project_dir, run_number)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate JSON input for HADDOCK and run haddock-restraints.")
    parser.add_argument("--entries", type=str, required=True,
                        help="JSON string of entries. Example: '[{\"id\": 1, \"chain\": \"A\", \"active\": [29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 93, 94, 95, 97, 99, 100, 101], \"passive\": [], \"structure\": \"protein1_orig.pdb\", \"target\": [2], \"passive_from_active\": true, \"filter_buried\": true}, {\"id\": 2, \"chain\": \"B\", \"active\": [8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 79, 82, 83, 85, 86], \"passive\": [], \"structure\": \"protein2_orig.pdb\", \"target\": [1], \"passive_from_active\": true, \"filter_buried\": true}]'")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    generator = HaddockInputGenerator(args.entries)
    generator.main()
    print("success")
