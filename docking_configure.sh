#!/bin/bash

#===============================================================================
# Docking Environment Configuration
#
# このスクリプトを使用する前に、以下のパスを環境に合わせて設定してください
#===============================================================================

#-------------------------------------------------------------------------------
# ユーザー設定セクション（要変更）
#-------------------------------------------------------------------------------
# TODO: 以下のパスを実際のインストール場所に変更してください

# ZDOCK のインストールパス
ZDOCK="/path/to/zdock"

# HADDOCK のインストールパス  
HADDOCK="/path/to/haddock"

# HADDOCK Restraints ツールのパス
HADDOCK_RESTRAINTS="/path/to/haddock-restraints"

#-------------------------------------------------------------------------------
# 自動設定セクション
#-------------------------------------------------------------------------------

# GROMACS の自動検出
GROMACS=$(command -v gmx 2>/dev/null || command -v gmx_mpi 2>/dev/null)
if [[ -z "$GROMACS" ]]; then
    echo "Warning: GROMACS (gmx) not found in PATH." >&2
    echo "Please install GROMACS or add it to your PATH if needed." >&2
fi

# HADDOCK Tools パスの設定
HADDOCKTOOLS="$HADDOCK/tools"

# Python パスの設定（既存のPYTHONPATHに追加）
if [[ -n "${PYTHONPATH:-}" ]]; then
    PYTHONPATH="${PYTHONPATH}:$HADDOCK"
else
    PYTHONPATH="$HADDOCK"
fi

# 環境変数のエクスポート
export ZDOCK HADDOCK HADDOCKTOOLS HADDOCK_RESTRAINTS GROMACS PYTHONPATH

#-------------------------------------------------------------------------------
# ライブラリパスの設定
#-------------------------------------------------------------------------------

# スクリプトディレクトリの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# lib64 を LD_LIBRARY_PATH に追加
LIB64_PATH="$SCRIPT_DIR/lib64"
if [[ -d "$LIB64_PATH" ]]; then
    if [[ -n "${LD_LIBRARY_PATH:-}" ]]; then
        export LD_LIBRARY_PATH="$LIB64_PATH:$LD_LIBRARY_PATH"
    else
        export LD_LIBRARY_PATH="$LIB64_PATH"
    fi
fi

#-------------------------------------------------------------------------------
# 設定確認
#-------------------------------------------------------------------------------

echo "=== Docking Environment Configured ==="
echo "ZDOCK: $ZDOCK"
echo "HADDOCK: $HADDOCK" 
echo "HADDOCK_RESTRAINTS: $HADDOCK_RESTRAINTS"
echo "GROMACS: ${GROMACS:-Not found}"
echo "======================================="
