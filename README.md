# Avatar Overlay 🎭

コーディングエージェントの動作を視覚化する小窓キャラクターオーバーレイ。

## 特徴

- 🖼️ 透明背景・常に最前面の小窓表示
- 📁 ファイルシステムの変更を監視して状態を推定
- 📜 ログファイルの監視でより正確な状態把握（オプション）
- 🎨 6種類の状態アニメーション
- 🖱️ ドラッグで位置移動可能

## 状態一覧

| 状態 | 説明 | トリガー |
|------|------|----------|
| `idle` | 待機中 | 活動がない時 |
| `thinking` | 考え中 | 最近活動があった後の静止期間 |
| `typing` | 入力中 | ファイルの更新が検出された時 |
| `running` | 実行中 | ログに実行パターンが検出された時 |
| `success` | 成功 | ログに成功パターンが検出された時 |
| `error` | エラー | ログにエラーパターンが検出された時 |

## インストール

```bash
# 仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate

# 依存パッケージをインストール
pip install PySide6 watchdog Pillow
```

## 使い方

### 基本的な使い方

```bash
# 仮想環境を有効化
source .venv/bin/activate

# プロジェクトディレクトリとアセットディレクトリを指定して起動
python avatar_overlay.py <project_dir> <assets_dir>

# 例：現在のディレクトリを監視
python avatar_overlay.py . ./assets
```

### ログファイルの監視も追加

```bash
python avatar_overlay.py . ./assets --log agent.log
```

### 除外ディレクトリを追加

```bash
python avatar_overlay.py . ./assets --exclude .cache,tmp,logs
```

## AIエージェントとの連携

AIエージェントと状態を同期させることで、あたかも「AIパートナー」が実在して作業しているような体験を作れます。

1. **連携用ログファイルの作成**
   
   適当な名前で空のログファイルを作成します。
   ```bash
   touch tya_status.log
   ```

2. **ログ監視モードで起動**
   
   作成したログファイルを `--log` オプションで指定して起動します。
   ```bash
   python avatar_overlay.py . ./assets --log tya_status.log
   ```

3. **状態のコントロール**
   
   エージェント側からこのログファイルに追記することで、状態をコントロールできます。
   
   | 状態 | キーワード例 | コマンド例 |
   |------|------------|------------|
   | **実行中** | `running`, `executing` | `echo "running task..." >> tya_status.log` |
   | **成功** | `success`, `completed` | `echo "task completed successfully" >> tya_status.log` |
   | **エラー** | `error`, `failed` | `echo "error occurred" >> tya_status.log` |
   | **考え中** | (ログ更新のみ) | `echo "thinking..." >> tya_status.log` |

   ※ エージェントに「作業開始時にログに書き込んで」と指示するか、ワークフローに組み込むと効果的です。

## アセット仕様

`assets` ディレクトリ内に**キャラクターごとのサブディレクトリ**を作成し、各状態のGIFファイルを配置してください：

```
assets/
├── default/          # キャラクター1（デフォルト）
│   ├── idle.gif
│   ├── thinking.gif
│   ├── typing.gif
│   ├── running.gif
│   ├── success.gif
│   └── error.gif
├── assistant/        # キャラクター2
│   ├── idle.gif
│   └── ...
└── cat/              # キャラクター3
    └── ...
```

### 必要なGIFファイル

各キャラクターディレクトリには以下のGIFを配置：

| ファイル | 説明 |
|---------|------|
| `idle.gif` | 待機アニメーション |
| `thinking.gif` | 考え中アニメーション |
| `typing.gif` | タイピングアニメーション |
| `running.gif` | 実行中アニメーション |
| `success.gif` | 成功アニメーション |
| `error.gif` | エラーアニメーション |

### 推奨仕様

- サイズ: 256×256 px
- 背景: 透過（アルファチャンネル）
- ループ: 自然に繋がる短ループ（0.8〜2.5秒程度）

## キャラ切替

複数のキャラクターパックを配置すると、**右クリックメニュー**から「🎭 キャラ切替」でリアルタイムに切り替えられます。

選択したキャラクターは `config.json` に自動保存され、次回起動時に復元されます。

## 仮素材の生成

テスト用の仮素材を生成するには：

```bash
python generate_placeholders.py
```

## ファイル構成

```
avatar_overlay/
├── avatar_overlay.py       # メインアプリケーション
├── generate_placeholders.py # 仮素材生成スクリプト
├── README.md               # このファイル
├── assets/                 # アニメーション素材
│   ├── default/            # デフォルトキャラクター
│   │   ├── idle.gif
│   │   ├── thinking.gif
│   │   ├── typing.gif
│   │   ├── running.gif
│   │   ├── success.gif
│   │   └── error.gif
│   └── (other_characters)/ # 追加キャラクター
└── .venv/                  # Python仮想環境
```

## トラブルシューティング

### WSL2でGUIが表示されない

WSLgが有効になっているか確認してください：
```bash
echo $DISPLAY  # :0 などが表示されればOK
```

表示されない場合は、Windows側でWSL2のバージョンを更新してください。

### 「Missing asset」警告が出る

アセットディレクトリに必要なGIFファイルがあるか確認してください。
