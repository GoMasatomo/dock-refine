# Dock-Refine

このプロジェクトは、タンパク質間ドッキングのための自動化パイプラインです。ZDOCK、HADDOCK、GROMACSなどのツールを使用して、効率的なタンパク質-タンパク質相互作用の予測を行います。

## 概要

このパイプラインは、タンパク質間ドッキング予測のための包括的なワークフローを提供し、以下の6つのステップを自動化します：

### 1. **ZDOCKを使用したドッキング計算** 
初期ドッキングポーズの網羅的生成
- **目的**: レセプターとリガンドの可能な結合モードを広範囲にサンプリング
- **手法**: FFT（高速フーリエ変換）ベースの剛体ドッキングアルゴリズム
- **処理内容**:
  - 各タンパク質表面の溶媒アクセス可能領域をマーキング（`mark_sur`）
  - 2000個の初期ドッキング配置を生成（デフォルト設定）
  - ZDOCKスコアに基づいて上位100個の構造を選択
  - ランダムシード使用による再現性確保
- **出力**: `complex.1.pdb` ～ `complex.100.pdb`（100個のドッキングポーズ）

### 2. **クラスタリング**
構造類似性に基づくPDBファイルのグループ化
- **目的**: 類似した結合モードを持つ構造をまとめ、代表的なポーズを特定
- **手法**: GROMACS `gmx cluster`を使用したRMSDベースクラスタリング
- **パラメータ**:
  - カットオフ距離: デフォルト0.45 nm（4.5 Å）（`-t`オプションで変更可能）
  - 距離計算対象: 全重原子のRMSD
  - 最大クラスター数: デフォルト3個（`-c`オプションで変更可能）
- **処理内容**:
  - 100個の構造を相互比較してRMSD行列を計算
  - 階層クラスタリングによるグループ化
  - 各クラスターの中心構造（centroid）を特定
- **出力**: `cluster_*.csv`（クラスタリング結果テーブル）

### 3. **インターフェイス残基の抽出**
タンパク質間接触部位の自動特定
- **目的**: タンパク質間相互作用に重要な残基を特定し、HADDOCK制約として利用
- **手法**: 距離ベースの接触残基検出
- **パラメータ**:
  - 距離カットオフ: デフォルト8.0 Å（重原子間距離）（`-d`オプションで変更可能）
  - 対象チェーン: A（レセプター）とB（リガンド）
- **処理内容**:
  - 各クラスターの代表構造を解析
  - チェーンA・B間で指定距離以内に重原子を持つ残基を抽出
  - 残基番号リストをJSON形式で保存
- **出力**: チェーン別のインターフェイス残基リスト

### 4. **HADDOCK入力ファイルの生成**
精密化計算のための設定ファイル自動作成
- **目的**: 各クラスターに対してHADDOCK計算用の設定を準備
- **生成ファイル**:
  - `run.param`: HADDOCK実行パラメータファイル
  - `ambig.tbl`: 曖昧な距離制約ファイル
  - その他必要な設定ファイル
- **制約設定**:
  - アクティブ残基: インターフェイス残基を使用
  - パッシブ残基: アクティブ残基周辺の隣接残基
  - ターゲット設定: レセプター（ID:1）⇄ リガンド（ID:2）の相互作用
- **出力**: 各クラスターディレクトリ（`Pos1/`, `Pos2/`, `Pos3/`）内の設定ファイル

### 5. **HADDOCKを使用したドッキング計算**
高精度な構造精密化とスコアリング
- **目的**: ZDOCKで得られた初期構造をエネルギー最小化により精密化
- **手法**: 分子動力学シミュレーションベースの段階的精密化
- **計算段階**:
  - **it0**: 剛体ドッキング（rigid body docking）
  - **it1**: 柔軟性を考慮した精密化（flexible refinement）
  - **water**: 明示的溶媒中での最終精密化
- **エネルギー項**:
  - `Evdw`: ファンデルワールス相互作用エネルギー
  - `Eelec`: 静電相互作用エネルギー  
  - `Edesolv`: 脱溶媒化エネルギー
- **出力**: `run1/structures/it1/water/`内の精密化構造群

### 6. **代表構造の抽出とエネルギー解析**
最終結果の評価と最適構造選択
- **目的**: 各クラスターから最良の構造を選択し、総合評価を実施
- **解析内容**:
  - HADDOCKスコア（`Evdw + Eelec + Edesolv`）の計算
  - クラスター内での構造ランキング
  - 統計的な品質評価（Z-score等）
- **選択基準**:
  - 最低エネルギー構造の特定
  - クラスター人口（cluster population）の考慮
  - 構造的妥当性の検証
- **統合処理**:
  - 全クラスターの結果を`combined_results.csv`に統合
  - 代表構造ファイルをメインディレクトリにコピー
  - 総合スコアによる最終ランキング作成
- **出力**: 
  - `combined_results.csv`: 全結果統合テーブル
  - 代表構造PDBファイル群
  - 各種エネルギー解析結果

### ワークフローの特徴
- **並列処理**: 複数クラスターのHADDOCK計算を同時実行
- **品質管理**: 各段階でエラーチェックと妥当性検証を実施
- **柔軟性**: パラメータ調整による計算精度とコストのバランス調整可能
- **再現性**: 固定シードと詳細ログによる結果の再現性確保

## 必要な環境

### 必要なソフトウェア
- Python 3.x
- ZDOCK
- HADDOCK 2.4
- GROMACS
- pandas
- その他のPythonライブラリ（requirements.ymlを参照）

### 環境変数の設定

#### 方法1: 設定スクリプトの使用（推奨）

`docking_configure.sh`を使用して環境を設定できます。**初回使用時は必ずパスの設定が必要です**：

1. **設定ファイルの編集**
   ```bash
   vim docking_configure.sh  # または他のエディタを使用
   ```

2. **ユーザー設定セクションの変更**
   
   ファイル内の以下の部分を実際のインストールパスに変更してください：
   ```bash
   #-------------------------------------------------------------------------------
   # ユーザー設定セクション（要変更）
   #-------------------------------------------------------------------------------
   # TODO: 以下のパスを実際のインストール場所に変更してください

   # ZDOCK のインストールパス
   ZDOCK="/path/to/zdock"  # 例: "/opt/zdock3.0.2_linux_x64"

   # HADDOCK のインストールパス  
   HADDOCK="/path/to/haddock"  # 例: "/opt/haddock2.4-2024-03"

   # HADDOCK Restraints ツールのパス
   HADDOCK_RESTRAINTS="/path/to/haddock-restraints"  # 例: "/opt/haddock-restraints-v0.7.0-x86_64-unknown-linux-gnu"
   ```

3. **設定の適用**
   ```bash
   source docking_configure.sh
   ```

   設定が正常に適用されると、以下のような出力が表示されます：
   ```
   === Docking Environment Configured ===
   ZDOCK: /opt/zdock3.0.2_linux_x64
   HADDOCK: /opt/haddock2.4-2024-03
   HADDOCK_RESTRAINTS: /opt/haddock-restraints-v0.7.0-x86_64-unknown-linux-gnu
   GROMACS: /usr/local/bin/gmx
   =======================================
   ```

#### 方法2: 手動での環境変数設定

設定スクリプトを使用しない場合は、以下の環境変数を手動で設定してください：

```bash
export ZDOCK=/path/to/zdock
export HADDOCK=/path/to/haddock
export HADDOCK_RESTRAINTS=/path/to/haddock-restraints
export GROMACS=/path/to/gromacs  # 通常は自動検出されます
```

#### 設定の確認

環境変数が正しく設定されているか確認するには：
```bash
echo "ZDOCK: $ZDOCK"
echo "HADDOCK: $HADDOCK"
echo "HADDOCK_RESTRAINTS: $HADDOCK_RESTRAINTS"
echo "GROMACS: $GROMACS"
```

## インストール

1. リポジトリのクローン：
```bash
git clone <repository-url>
cd docking
```

2. 必要なPythonパッケージのインストール：
```bash
conda env create -f requirements.yml
conda activate dock-refine
```

## 使用方法

### 基本的な使用方法

```bash
conda activate dock-refine
python run_docking.py <receptor.pdb> <ligand.pdb> [-o output_directory] [-c max_clusters] [-d interface_distance] [-t cluster_cutoff]
```

### パラメータ

- `receptor.pdb`: レセプタータンパク質のPDBファイル
- `ligand.pdb`: リガンドタンパク質のPDBファイル  
- `-o, --output`: 出力ディレクトリのパス（デフォルト: `results`）
- `-c, --max-clusters`: 処理する最大クラスター数（デフォルト: `3`）
- `-d, --interface-distance`: インターフェイス残基の距離カットオフ (Å)（デフォルト: `8.0`）
- `-t, --cluster-cutoff`: クラスタリングの距離カットオフ (nm)（デフォルト: `0.45`）

### 使用例

```bash
# 基本的な実行（デフォルト: 最大3クラスター、距離8.0Å、カットオフ0.45nm）
python run_docking.py 7OPB_A.pdb 7OPB_B.pdb

# 出力ディレクトリを指定
python run_docking.py 7OPB_A.pdb 7OPB_B.pdb -o my_results

# 最大クラスター数を指定（例: 5クラスター）
python run_docking.py 7OPB_A.pdb 7OPB_B.pdb -c 5

# インターフェイス残基の距離カットオフを変更（例: 6.0Å）
python run_docking.py 7OPB_A.pdb 7OPB_B.pdb -d 6.0

# クラスタリングの距離カットオフを変更（例: 0.3nm）
python run_docking.py 7OPB_A.pdb 7OPB_B.pdb -t 0.3

# 全オプションを指定
python run_docking.py 7OPB_A.pdb 7OPB_B.pdb -o my_results -c 5 -d 6.0 -t 0.3
```

## 入力ファイルの準備

### 重要な注意事項
- **ATOM、TER、END行以外**が入力PDBファイルに含まれると予測が正常に実行されない場合があります
- PDBファイルは適切にクリーンアップされている必要があります
- 各チェーンが正しく識別されていることを確認してください

### PDBファイルの前処理
```bash
# 不要な行を削除（例）
grep -E "^(ATOM|TER|END)" input.pdb > cleaned_input.pdb
```

## 出力ファイル

パイプライン実行後、以下のファイルが生成されます：

### メインディレクトリ
- `combined_results.csv`: 全クラスターの解析結果統合ファイル
- `*.pdb`: 代表構造ファイル

### dockingディレクトリ
- `zdock.out`: ZDOCKの出力ファイル
- `complex.*.pdb`: 生成されたドッキングポーズ（1-100番）
- `cluster_*.csv`: クラスタリング結果

### 各クラスターディレクトリ（Pos1, Pos2, Pos3）
- `run.param`: HADDOCK設定ファイル
- `run1/`: HADDOCK計算結果
  - `structures/it1/water/`: 最終構造ファイル
  - 各種エネルギーファイル

## モジュール構成

### dockmodules/
- `run_zdock.py`: ZDOCK実行モジュール
- `run_clustering.py`: クラスタリング実行モジュール
- `get_interface_residue.py`: インターフェイス残基抽出
- `get_haddock_input.py`: HADDOCK入力ファイル生成
- `run_haddock.py`: HADDOCK実行モジュール
- `haddock_analysis.py`: HADDOCK結果解析

### assessment/
- `interface_contact_score_calculator.py`: インターフェイス接触スコア計算

## パイプライン詳細

### 1. ZDOCK計算
- 受容体と配位子の表面をマーキング
- 2000個の初期ドッキングポーズを生成
- 上位100個を選択して後続解析に使用

### 2. クラスタリング
- GROMACSを使用してRMSDベースでクラスタリング
- カットオフ距離: デフォルト0.45 nm（`-t`オプションで変更可能）
- 最大クラスター数: デフォルト3個（`-c`オプションで変更可能）

### 3. HADDOCK精密化
- 各クラスターの代表構造に対して実行
- インターフェイス残基を制約として使用
- 距離カットオフ: デフォルト8.0 Å（`-d`オプションで変更可能）

### 4. 結果解析
- エネルギー項目（Evdw, Eelec, Edesolv）の統合
- 代表構造の抽出
- 総合スコアの計算

## トラブルシューティング

### よくあるエラー

1. **環境変数エラー**
   ```
   EnvironmentError: 必要な環境変数 (ZDOCK, HADDOCK, GROMACS) が設定されていません。
   ```
   **解決方法:**
   - `docking_configure.sh`内のパス設定を確認
   - 実際のインストールパスに変更されているか確認
   - `source docking_configure.sh`を実行して設定を適用

2. **パス設定エラー**
   ```
   Warning: ZDOCK directory not found: /path/to/zdock
   ```
   **解決方法:**
   - `docking_configure.sh`のユーザー設定セクションを編集
   - デフォルトの`/path/to/zdock`を実際のパスに変更
   - ディレクトリの存在と読み取り権限を確認

3. **PDBファイルエラー**
   - ATOM/TER/END行以外が含まれている
   **解決方法:** PDBファイルをクリーンアップしてください

4. **メモリエラー**
   - 並列処理でメモリ不足
   **解決方法:** プロセス数を調整するか、より多くのメモリを割り当ててください

### ログの確認
各段階での詳細なログは対応するディレクトリ内で確認できます：
- ZDOCK: `zdock.out`
- クラスタリング: `cluster.log`
- HADDOCK: `run1/`ディレクトリ内の各種ログファイル

## 関連ファイル

- `docking_configure.sh`: 環境設定スクリプト
- `requirements.yml`: 必要なPythonパッケージ
- `Test/`: テスト用ファイルとサンプルデータ

## ライセンス

このプロジェクトで使用されるツールのライセンスに従ってください：
- ZDOCK: 各自ライセンスを確認
- HADDOCK: 学術利用は無料
- GROMACS: LGPLライセンス

## 引用

このパイプラインを使用して研究を行った場合は、使用したツールの論文を適切に引用してください。

## サポート

問題や質問がある場合は、各ツールの公式ドキュメントを参照するか、開発者にお問い合わせください。
