#!/usr/bin/env python3
"""
キャラクター作成ツール - PNG素材から新しいキャラクターパックを生成

使用例:
    # 基本: PNGフォルダから新キャラを作成
    python create_character.py tya-san ./my_pngs/
    
    # フレーム間隔を指定
    python create_character.py tya-san ./my_pngs/ --duration 400
    
    # 状態ごとに別の間隔を指定
    python create_character.py tya-san ./my_pngs/ --idle-duration 600 --typing-duration 200

PNG素材の命名規則:
    idle01.png, idle02.png, ...      → idle.gif
    thinking01.png, thinking02.png   → thinking.gif
    typing01.png, typing02.png       → typing.gif (または type01.png)
    running01.png, running02.png     → running.gif (または talking01.png)
    success01.png, success02.png     → success.gif
    error01.png, error02.png         → error.gif
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image


# 状態とPNGパターンのマッピング（優先順位順）
STATE_PATTERNS = {
    "idle": ["idle"],
    "thinking": ["thinking"],
    "typing": ["typing", "type"],
    "running": ["running", "talking"],
    "success": ["success"],
    "error": ["error"],
}

# デフォルトのフレーム間隔（ミリ秒）
DEFAULT_DURATIONS = {
    "idle": 500,
    "thinking": 600,
    "typing": 200,
    "running": 300,
    "success": 500,
    "error": 500,
}


def find_png_files(folder: Path, patterns: list[str]) -> list[Path]:
    """
    指定パターンに一致するPNGファイルを探す
    
    Args:
        folder: 検索するフォルダ
        patterns: ファイル名の先頭パターン（優先順位順）
    
    Returns:
        見つかったPNGファイルのリスト（ソート済み）
    """
    for pattern in patterns:
        files = sorted([
            f for f in folder.iterdir()
            if f.name.lower().startswith(pattern) and f.suffix.lower() == ".png"
        ])
        if files:
            return files
    return []


def create_gif(png_files: list[Path], output_path: Path, duration: int = 500) -> bool:
    """
    PNG画像からGIFアニメーションを作成
    
    Args:
        png_files: PNG画像のパスリスト
        output_path: 出力するGIFファイルのパス
        duration: フレーム間の時間(ミリ秒)
    
    Returns:
        成功したかどうか
    """
    if not png_files:
        return False
    
    images = []
    for png_file in png_files:
        img = Image.open(png_file)
        # RGBAモードに変換(透過対応)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        images.append(img)
    
    # GIFとして保存
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:] if len(images) > 1 else [],
        duration=duration,
        loop=0,  # 無限ループ
        optimize=False,
        disposal=2,  # 前のフレームをクリアしてから次のフレームを描画
    )
    
    return True


def create_character(
    name: str,
    source_folder: Path,
    output_folder: Path,
    durations: dict[str, int],
    verbose: bool = True,
) -> dict[str, bool]:
    """
    PNG素材から新しいキャラクターパックを作成
    
    Args:
        name: キャラクター名
        source_folder: PNG素材が入っているフォルダ
        output_folder: 出力先のベースフォルダ（assets/）
        durations: 各状態のフレーム間隔
        verbose: 詳細出力するかどうか
    
    Returns:
        各状態の作成結果
    """
    char_folder = output_folder / name
    char_folder.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for state, patterns in STATE_PATTERNS.items():
        png_files = find_png_files(source_folder, patterns)
        output_path = char_folder / f"{state}.gif"
        duration = durations.get(state, 500)
        
        if png_files:
            success = create_gif(png_files, output_path, duration)
            results[state] = success
            
            if verbose:
                if success:
                    used_pattern = png_files[0].name.split("0")[0].rstrip("_-")
                    print(f"  ✅ {state}.gif ({len(png_files)}フレーム, {duration}ms) ← {used_pattern}*.png")
                else:
                    print(f"  ❌ {state}.gif - 作成に失敗しました")
        else:
            results[state] = False
            if verbose:
                print(f"  ⚠️  {state}.gif - 素材が見つかりませんでした")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="PNG素材から新しいキャラクターパックを作成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python create_character.py tya-san ./my_pngs/
  python create_character.py robot ./robot_pngs/ --duration 300
  python create_character.py cat ./cat_pngs/ --typing-duration 150

PNG素材の命名規則:
  idle01.png, idle02.png, ...    → idle.gif
  thinking01.png, ...            → thinking.gif
  typing01.png or type01.png     → typing.gif
  running01.png or talking01.png → running.gif
  success01.png, ...             → success.gif
  error01.png, ...               → error.gif
        """
    )
    
    parser.add_argument(
        "name",
        help="キャラクター名（assets/[name]/ に出力される）"
    )
    parser.add_argument(
        "source",
        help="PNG素材が入っているフォルダのパス"
    )
    parser.add_argument(
        "-o", "--output",
        default="./assets",
        help="出力先ベースフォルダ (デフォルト: ./assets)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=None,
        help="全状態共通のフレーム間隔(ms)"
    )
    
    # 状態ごとのdurationオプション
    for state in STATE_PATTERNS.keys():
        parser.add_argument(
            f"--{state}-duration",
            type=int,
            default=None,
            help=f"{state}のフレーム間隔(ms) (デフォルト: {DEFAULT_DURATIONS[state]})"
        )
    
    args = parser.parse_args()
    
    # パスの解決
    script_dir = Path(__file__).parent
    source_folder = Path(args.source)
    if not source_folder.is_absolute():
        source_folder = script_dir / source_folder
    
    output_folder = Path(args.output)
    if not output_folder.is_absolute():
        output_folder = script_dir / output_folder
    
    # 素材フォルダの確認
    if not source_folder.exists():
        print(f"❌ エラー: 素材フォルダが見つかりません: {source_folder}")
        return 1
    
    # durationの解決
    durations = DEFAULT_DURATIONS.copy()
    if args.duration:
        # 全体のdurationが指定されている場合
        durations = {state: args.duration for state in STATE_PATTERNS}
    
    # 個別のduration指定を上書き
    for state in STATE_PATTERNS.keys():
        state_duration = getattr(args, f"{state}_duration".replace("-", "_"))
        if state_duration is not None:
            durations[state] = state_duration
    
    # キャラクター作成
    print(f"🎭 キャラクター「{args.name}」を作成中...")
    print(f"📁 素材: {source_folder}")
    print(f"📂 出力: {output_folder / args.name}")
    print()
    
    results = create_character(
        name=args.name,
        source_folder=source_folder,
        output_folder=output_folder,
        durations=durations,
    )
    
    # 結果サマリー
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print()
    if success_count == total_count:
        print(f"🎉 完了！{success_count}/{total_count} 個のアニメーションを作成しました")
    elif success_count > 0:
        print(f"⚠️  {success_count}/{total_count} 個のアニメーションを作成しました")
        print("   足りない素材を追加して再実行するか、既存キャラからコピーしてください")
    else:
        print("❌ アニメーションを作成できませんでした")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
