#!/usr/bin/env python3
"""
GIFアニメーションをリサイズするスクリプト
"""
from PIL import Image
import os
import sys
import argparse
import glob

def resize_gif(input_path, output_path, width=None, height=None, scale=None):
    """
    GIFアニメーションをリサイズ
    
    Args:
        input_path: 入力GIFファイルのパス
        output_path: 出力GIFファイルのパス
        width: 目標の幅(px) - heightと排他
        height: 目標の高さ(px) - widthと排他
        scale: スケール倍率(例: 0.5で半分) - width/heightと排他
    """
    # GIFを開く
    gif = Image.open(input_path)
    
    # 元のサイズ
    original_size = gif.size
    print(f"📏 元のサイズ: {original_size[0]}x{original_size[1]}px")
    
    # 新しいサイズを計算
    if scale:
        new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
    elif width:
        aspect_ratio = original_size[1] / original_size[0]
        new_size = (width, int(width * aspect_ratio))
    elif height:
        aspect_ratio = original_size[0] / original_size[1]
        new_size = (int(height * aspect_ratio), height)
    else:
        print("❌ エラー: width, height, scaleのいずれかを指定してください")
        return False
    
    print(f"🎯 新しいサイズ: {new_size[0]}x{new_size[1]}px")
    
    # 全フレームをリサイズ
    frames = []
    durations = []
    
    try:
        while True:
            # フレームをリサイズ
            frame = gif.copy()
            # RGBAモードに変換してからリサイズ（画質向上）
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
            frame = frame.resize(new_size, Image.Resampling.LANCZOS)
            # Pモードに最適化変換（ディザリング適用）
            frame = frame.convert('P', palette=Image.ADAPTIVE, colors=256, dither=Image.FLOYDSTEINBERG)
            frames.append(frame)
            
            # フレームの表示時間を取得
            durations.append(gif.info.get('duration', 100))
            
            # 次のフレームへ
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass  # 全フレーム処理完了
    
    # リサイズしたGIFを保存（最適化ON！）
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=gif.info.get('loop', 0),
        optimize=True,  # 🎨 optimize=True で画質向上！
        disposal=2,
        transparency=0  # 透過色のインデックスを指定
    )
    
    print(f"✓ リサイズ完了: {output_path}")
    print(f"  - フレーム数: {len(frames)}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='GIFアニメーションをリサイズ')
    parser.add_argument('input', help='入力GIFファイル (ワイルドカード可: *.gif)')
    parser.add_argument('-w', '--width', type=int, help='目標の幅(px)')
    parser.add_argument('-H', '--height', type=int, help='目標の高さ(px)')
    parser.add_argument('-s', '--scale', type=float, help='スケール倍率 (例: 0.5で半分)')
    parser.add_argument('-o', '--output', help='出力ファイル名 (複数ファイル時は無視)')
    parser.add_argument('--suffix', default='_resized', help='出力ファイルのサフィックス (デフォルト: _resized)')
    parser.add_argument('--overwrite', action='store_true', help='元ファイルを上書き')
    
    args = parser.parse_args()
    
    # サイズ指定のチェック
    size_options = sum([args.width is not None, args.height is not None, args.scale is not None])
    if size_options != 1:
        print("❌ エラー: --width, --height, --scaleのいずれか1つを指定してください")
        return 1
    
    # 入力ファイルを取得
    input_files = glob.glob(args.input)
    if not input_files:
        print(f"❌ エラー: {args.input} に一致するファイルが見つかりません")
        return 1
    
    print(f"🎬 処理するファイル: {len(input_files)}個\n")
    
    # 各ファイルを処理
    for input_path in input_files:
        print(f"📂 処理中: {input_path}")
        
        # 出力パスを決定
        if args.overwrite:
            output_path = input_path
        elif args.output and len(input_files) == 1:
            output_path = args.output
        else:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}{args.suffix}{ext}"
        
        # リサイズ実行
        success = resize_gif(input_path, output_path, args.width, args.height, args.scale)
        
        if not success:
            return 1
        
        print()
    
    print("🎉 全ての処理が完了しました！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
