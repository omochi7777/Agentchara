#!/usr/bin/env python3
"""
talking*.pngからrunning.gifを作成するスクリプト
"""
from PIL import Image
import os

def create_gif_from_pngs(png_folder, pattern, output_path, duration=500, loop=0):
    """
    指定フォルダ内のPNG画像からGIFアニメーションを作成
    
    Args:
        png_folder: PNG画像が入っているフォルダパス
        pattern: ファイル名のパターン(例: "talking")
        output_path: 出力するGIFファイルのパス
        duration: フレーム間の時間(ミリ秒)
        loop: ループ回数(0=無限ループ)
    """
    # PNG画像を取得してソート
    png_files = sorted([f for f in os.listdir(png_folder) 
                       if f.startswith(pattern) and f.endswith('.png')])
    
    if len(png_files) < 2:
        print(f"エラー: {png_folder}に{pattern}で始まる2枚以上のPNG画像が必要です")
        return
    
    print(f"見つかった画像: {png_files}")
    
    # 画像を読み込み
    images = []
    for png_file in png_files:
        img_path = os.path.join(png_folder, png_file)
        img = Image.open(img_path)
        # RGBAモードに変換(透過対応)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        images.append(img)
    
    # GIFとして保存
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=False,
        disposal=2  # 前のフレームをクリアしてから次のフレームを描画
    )
    
    print(f"✓ GIFを作成しました: {output_path}")
    print(f"  - フレーム数: {len(images)}")
    print(f"  - フレーム間隔: {duration}ms")
    print(f"  - ループ: {'無限' if loop == 0 else f'{loop}回'}")

if __name__ == "__main__":
    # 設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    png_folder = os.path.join(script_dir, "assets", "png")
    output_path = os.path.join(script_dir, "assets", "running.gif")
    
    # GIF作成 (talking*.png → running.gif)
    create_gif_from_pngs(png_folder, "talking", output_path, duration=500, loop=0)
