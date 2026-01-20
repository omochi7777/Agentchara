# Windowsでのセットアップ手順

WSL2環境ではオーバーレイを最前面に表示し続けることが難しいため、アプリケーション自体をWindows側で実行します。
これにより、VS CodeなどのWindowsアプリケーションよりも手前に表示させることが可能になります。

## 1. 準備

### 1-1. Pythonの確認
Windowsのコマンドプロンプト（またはPowerShell）を開き、Pythonがインストールされているか確認してください。

```powershell
python --version
```

バージョンが表示されない場合は、[Python公式サイト](https://www.python.org/downloads/) または Microsoft Store からインストールしてください。

### 1-2. ファイルの準備
現在の `avatar_overlay` フォルダを、Windows側の適当な場所（デスクトップなど）にコピーしてください。
※ WSL上のファイルを直接実行することも可能ですが、パスの扱いが複雑になるため、コピーを推奨します。

例：
1. Windowsのエクスプローラーで `\\wsl.localhost\[ディストリビューション名]\home\[ユーザー名]\agent\avatar_overlay` を開く
   (例: `\\wsl.localhost\Ubuntu\home\ginnan\agent\avatar_overlay`)
2. フォルダごとデスクトップなどにコピーする

## 2. 環境構築

Windows側のコピーしたフォルダ内で、PowerShellを開き、以下のコマンドを実行してライブラリをインストールします。

```powershell
# フォルダへ移動 (例: デスクトップにコピーした場合)
cd $HOME\Desktop\avatar_overlay

# 仮想環境の作成（必須ではありませんが推奨）
python -m venv venv
.\venv\Scripts\Activate.ps1

# ※権限エラーが出る場合は以下を実行してから再度 activate
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# ライブラリのインストール
pip install PySide6 watchdog Pillow
```

## 3. 実行

Windows側でアプリケーションを起動します。

### 基本的な起動
```powershell
python avatar_overlay.py . ./assets
```

これでデスクトップに俺（月さん）が表示され、かつ他のウィンドウをクリックしても最前面に居座るはずです。

### Linux側のエージェントと連携する場合（重要）

Linux側で動いているエージェントのログ (`agent.log`) を監視させたい場合、WSLのパスを指定して起動します。

1. Linux側でのログファイルのフルパスを確認しておく
   例: `/home/ginnan/agent/avatar_overlay/agent.log`

2. Windows側からそのパスを指定して実行
   WSLのパスは `\\wsl.localhost\[ディストリビューション名]\...` に変換します。

```powershell
# 例: Ubuntuの場合
python avatar_overlay.py . ./assets --log "\\wsl.localhost\Ubuntu\home\ginnan\agent\avatar_overlay\agent.log"
```

※ ディストリビューション名が不明な場合は、PowerShellで `wsl --list` を実行して確認してください。

## 補足

- **終了方法**: タスクトレイには入らないので、実行しているコマンドプロンプトで `Ctrl+C` を押すか、オーバーレイを右クリックして「終了」を選んでください。
- **位置のリセット**: 変な場所にいってしまったら、右クリックメニューから位置をリセットできます。
