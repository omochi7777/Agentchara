#!/usr/bin/env python3
"""
PNG画像からGIFアニメーションを作成する汎用スクリプト
"""
from PIL import Image
import os
import sys
import argparse

def create_gif_from_pngs(png_folder, pattern, output_path, duration=500, loop=0):
    """
    指定フォルダ内のPNG画像からGIFアニメーションを作成
    
    Args:
        png_folder: PNG画像が入っているフォルダパス
        pattern: ファイル名のパターン(例: "idle", "talking")
        output_path: 出力するGIFファイルのパス
        duration: フレーム間の時間(ミリ秒)
        loop: ループ回数(0=無限ループ)
    """
    # PNG画像を取得してソート
    png_files = sorted([f for f in os.listdir(png_folder) 
                       if f.startswith(pattern) and f.endswith('.png')])
    
    if len(png_files) < 1:
        print(f"❌ エラー: {png_folder}に{pattern}で始まるPNG画像が見つかりません")
        return False
    
    print(f"📁 見つかった画像: {png_files}")
    
    # 画像を読み込み
    images = []
    for png_file in png_files:
        img_path = os.path.join(png_folder, png_file)
        img = Image.open(img_path)
        # RGBAモードに変換(透過対応)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        images.append(img)
    
    # 全フレームで統一パレットを作成（画質向上のため）
    # まず全フレームを結合してパレットを生成
    if images:
        # P+A モード（パレット+アルファチャンネル）に変換してGIF最適化
        optimized_images = []
        for img in images:
            # RGBAをPモードに変換（256色に最適化、ディザリング適用）
            p_img = img.convert('P', palette=Image.ADAPTIVE, colors=256, dither=Image.FLOYDSTEINBERG)
            optimized_images.append(p_img)
        images = optimized_images
    
    # GIFとして保存（最適化ON！）
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=True,  # 🎨 optimize=True で画質向上！
        disposal=2,  # 前のフレームをクリアしてから次のフレームを描画
        transparency=0  # 透過色のインデックスを指定
    )
    
    print(f"✓ GIFを作成しました: {output_path}")
    print(f"  - フレーム数: {len(images)}")
    print(f"  - フレーム間隔: {duration}ms")
    print(f"  - ループ: {'無限' if loop == 0 else f'{loop}回'}")
    return True

def main():
    parser = argparse.ArgumentParser(description='PNG画像からGIFアニメーションを作成')
    parser.add_argument('pattern', help='ファイル名のパターン (例: idle, talking, type)')
    parser.add_argument('-o', '--output', help='出力ファイル名 (デフォルト: [pattern].gif)')
    parser.add_argument('-d', '--duration', type=int, default=500, help='フレーム間隔(ms) (デフォルト: 500)')
    parser.add_argument('-l', '--loop', type=int, default=0, help='ループ回数 (0=無限, デフォルト: 0)')
    parser.add_argument('-f', '--folder', default='assets/png', help='PNG画像フォルダ (デフォルト: assets/png)')
    
    args = parser.parse_args()
    
    # パスの設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    png_folder = os.path.join(script_dir, args.folder)
    
    # 出力ファイル名の決定
    if args.output:
        output_filename = args.output if args.output.endswith('.gif') else f"{args.output}.gif"
    else:
        output_filename = f"{args.pattern}.gif"
    
    output_path = os.path.join(script_dir, "assets", output_filename)
    
    # GIF作成
    success = create_gif_from_pngs(png_folder, args.pattern, output_path, args.duration, args.loop)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
