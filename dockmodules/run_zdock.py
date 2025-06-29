#!/usr/bin/env python3
"""
このスクリプトは、タンパク質ドッキングツールZDOCKおよびその関連する前処理・後処理ステップを
実行するためのコマンドラインインターフェースを提供します。受容体およびリガンドのPDBファイルに
対して表面残基をマークし、ZDOCKによるドッキングプロセスを実行し、ドッキング予測を抽出する
機能を含みます。

スクリプトは、ZDOCKおよび関連ツールとのやり取りのロジックをカプセル化した`ZDockRunner`クラスを
定義します。また、コマンドライン引数を処理し、ドッキングワークフローを実行するための`main`関数を
含みます。

使用方法:
    必要な引数（受容体およびリガンドのPDBファイル）を指定してコマンドラインからスクリプトを実行します。
    オプションの引数を使用して、ドッキングプロセスをカスタマイズできます（例: 予測数、ランダム化シード、
    その他のZDOCKオプション）。

例:
    python run_zdock.py -R receptor.pdb -L ligand.pdb -o output.zdock -N 1000 -S 42 -D -F

環境変数:
    ZDOCK: ZDOCKおよびその関連ツール（例: `mark_sur`, `create.pl`, `create_lig`）を含む
    ディレクトリへのパス。この環境変数はスクリプトを実行する前に設定する必要があります。

依存関係:
    - Python 3.x
    - ZDOCKおよびその関連ツール
    - 必要な外部コマンド: `cp`

クラス:
    - ZDockRunner: ZDOCKおよびその前処理・後処理ステップを実行するロジックをカプセル化します。

関数:
    - main(): コマンドライン引数を解析し、ドッキングワークフローを実行します。

例外:
    - EnvironmentError: `ZDOCK`環境変数が設定されていない場合に発生します。
    - subprocess.CalledProcessError: 外部コマンドの実行が失敗した場合に発生します。
    - ValueError: 必要な入力ファイルまたはパラメータが不足している場合に発生します。

"""
import os
import subprocess as sp
import random
from pathlib import Path
import argparse

# Set zdock_dir_path to use ZDOCK commands
ZDOCK = os.environ.get("ZDOCK")


class ZDockRunner:
    """
    ZDockRunnerクラス
    このクラスは、ZDOCKプログラムを使用してタンパク質間のドッキングを実行するためのユーティリティを提供します。
    ZDOCKは、受容体とリガンドのPDBファイルを入力として受け取り、ドッキング予測を行います。
    使用例:
        # 環境変数 'ZDOCK' を設定しておく必要があります
        export ZDOCK=/path/to/zdock
        # ZDockRunnerのインスタンスを作成
        zdock_runner = ZDockRunner()
        # PDBファイルの表面残基をマーク
        zdock_runner.mark_sur("receptor.pdb", "receptor_marked.pdb")
        # ZDOCKを実行してドッキング予測を生成
        zdock_runner.run_zdock(
            receptor_pdb_path="receptor_marked.pdb",
            ligand_pdb_path="ligand.pdb",
            filename="zdock_output.out",
            num_predictions=2000,
            seed=42,
            is_dense_rot_samp=True,
            is_fix_receptor=False
        )
        # ZDOCKのアウトプットファイルを処理して予測構造を抽出
        zdock_runner.create_pl(zdock_output_file="zdock_output.out", num_preds=1000)
    メソッド:
        - __init__: クラスの初期化を行い、ZDOCKのパスを設定します。
        - mark_sur: PDBファイルの表面残基をマークします。
        - run_zdock: ZDOCKを実行してドッキング予測を生成します。
        - create_pl: ZDOCKのアウトプットファイルを処理し、予測構造を抽出します。
    注意:
        - このクラスを使用する前に、環境変数 'ZDOCK' を正しく設定してください。
        - 外部コマンドを実行するため、必要なスクリプトやバイナリが指定されたパスに存在することを確認してください。
    """
    def __init__(self):
        """
        ZDockRunnerクラスの初期化。

        例外:
            EnvironmentError: 環境変数 'ZDOCK' が設定されていない場合。
        """
        self.zdock_path = ZDOCK  # 環境変数から取得したZDOCKのパスを使用
        if not self.zdock_path:
            raise EnvironmentError("環境変数 'ZDOCK' が設定されていません。")
        self.zdock_output = None  # ZDOCKのアウトプットを保持するための属性

    def mark_sur(self, pdb_path: str, out_pdb_path: str):
        """
        指定されたPDBファイルの表面残基をマークし、結果を新しいPDBファイルとして出力します。

        引数:
            pdb_path (str): 表面残基をマークする対象のPDBファイルのパス。
            out_pdb_path (str): 表面残基がマークされた結果を保存する出力PDBファイルのパス。

        例外:
            subprocess.CalledProcessError: 外部コマンドの実行に失敗した場合。
        """
        
        # uniCHARMMファイルをカレントディレクトリにコピー
        cp_uniCHARMM_cmd = ["cp", f"{self.zdock_path}/uniCHARMM", ".", "-f"]
        sp.run(cp_uniCHARMM_cmd)

        # PDBファイルの表面残基をマークする
        mark_sur_cmd = [f"{self.zdock_path}/mark_sur", pdb_path, out_pdb_path]
        sp.run(mark_sur_cmd)

    def run_zdock(self, receptor_pdb_path: str,
                  ligand_pdb_path: str,
                  filename: str = "zdock.out",
                  num_predictions: int = 2000,
                  seed: int = random.randint(1, 100),
                  is_dense_rot_samp: bool = False,
                  is_fix_receptor: bool = False):
        """
        指定されたパラメータを使用してZDOCKを実行します。

        引数:
            receptor_pdb_path (str): 受容体PDBファイルのパス。
            ligand_pdb_path (str): リガンドPDBファイルのパス。
            filename (str, optional): 出力ファイル名 (デフォルトは "zdock.out")。
            num_predictions (int, optional): 出力する予測数 (デフォルトは2000)。
            seed (int, optional): ランダム化のシード値 (デフォルトは1から100のランダム整数)。
            is_dense_rot_samp (bool, optional): 高密度回転サンプリングを使用するか (デフォルトはFalse)。
            is_fix_receptor (bool, optional): 受容体を固定して回転を防ぐか (デフォルトはFalse)。

        例外:
            subprocess.CalledProcessError: ZDOCKコマンドの実行に失敗した場合。
        """
        
        # ZDOCKコマンドを構築する
        zdock_cmd = [f"{self.zdock_path}/zdock", "-R", receptor_pdb_path, "-L",
                     ligand_pdb_path, "-o", filename, "-N", str(num_predictions), "-S", str(seed)]
        if is_dense_rot_samp:
            zdock_cmd.append("-D")
        if is_fix_receptor:
            zdock_cmd.append("-F")
        sp.run(zdock_cmd)

        # ZDOCKのアウトプットファイルを保持
        self.zdock_output = filename

    def create_pl(self, zdock_output_file: str = None, num_preds: int = 2000):
        """
        ZDOCKによって生成されたアウトプットファイルを処理し、指定された数の予測ドッキング構造を抽出します。

        引数:
            zdock_output_file (str, optional): ZDOCKのアウトプットファイルのパス。
                指定されない場合は、`self.zdock_output` が使用されます。
            num_preds (int, optional): 抽出する予測構造の数 (デフォルトは2000)。

        例外:
            ValueError: ZDOCKのアウトプットファイルが指定されていない場合。
            subprocess.CalledProcessError: 必要なコマンドの実行に失敗した場合。
        """
        # 使用するアウトプットファイルを決定
        zdock_output_file = zdock_output_file or self.zdock_output
        if not zdock_output_file:
            raise ValueError("ZDOCKのアウトプットファイルが指定されていません。")

        # create_ligスクリプトをカレントディレクトリにコピー
        cp_create_lig_cmd = ["cp", f"{self.zdock_path}/create_lig", ".", "-f"]
        sp.run(cp_create_lig_cmd, check=True)

        # create.plスクリプトを実行
        create_pl_cmd = [f"{self.zdock_path}/create.pl", zdock_output_file, str(num_preds)]
        sp.run(create_pl_cmd, check=True)
            

def main():
    parser = argparse.ArgumentParser(description="ZDOCK")
    parser.add_argument("-R", "--receptor", required=True, help="受容体PDBファイルのパス。")
    parser.add_argument("-L", "--ligand", required=True, help="リガンドPDBファイルのパス。")
    parser.add_argument("-o", "--output", default="zdock.out", help="出力ファイル名 (デフォルト: zdock.out)。")
    parser.add_argument("-N", "--num_predictions", type=int, default=2000, help="予測数 (デフォルト: 2000)。")
    parser.add_argument("-S", "--seed", type=int, help="ランダム化シード (デフォルト: ランダム)。")
    parser.add_argument("-D", "--dense", action="store_true", help="高密度回転サンプリングを使用します。")
    parser.add_argument("-F", "--fix", action="store_true", help="受容体を固定して回転を防ぎます。")
    args = parser.parse_args()

    zdock_runner = ZDockRunner()

    # マークされたPDBファイルの出力ファイル名を生成
    receptor_m_out = Path(args.receptor).stem + "_m.pdb"
    ligand_m_out = Path(args.ligand).stem + "_m.pdb"
    
    # 受容体とリガンドの表面残基をマークする処理を開始
    zdock_runner.mark_sur(args.receptor, receptor_m_out)
    zdock_runner.mark_sur(args.ligand, ligand_m_out)
    
    # ZDOCKを実行
    seed = args.seed if args.seed is not None else random.randint(1, 100)
    zdock_runner.run_zdock(receptor_m_out, ligand_m_out, args.output, args.num_predictions, seed, args.dense, args.fix)

if __name__ == "__main__":
    main()