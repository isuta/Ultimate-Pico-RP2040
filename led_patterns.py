import config
from machine import Pin
import neopixel
import time

# NeoPixelストリップを保持する辞書
neo_strips = {}

def init_neopixels():
    """configに基づいてNeoPixelストリップを初期化します。"""
    global neo_strips
    for name, setup in config.NEOPIXEL_STRIPS.items():
        pin = Pin(setup['pin'], Pin.OUT)
        count = setup['count']
        strip = neopixel.NeoPixel(pin, count)
        neo_strips[name] = strip
        strip.fill((0, 0, 0)) # 初期は消灯
        strip.write()
        print(f"NeoPixel Strip '{name}' on GP{setup['pin']} with {count} LEDs initialized.")

def set_color(strip_name, color):
    """指定されたストリップ全体を指定された色に設定します。"""
    current_strip = neo_strips.get(strip_name)
    if current_strip:
        current_strip.fill(tuple(color))
        current_strip.write()
    else:
        print(f"Error: NeoPixel strip '{strip_name}' not found.")

def off(strip_name):
    """指定されたストリップを消灯させます。"""
    set_color(strip_name, [0, 0, 0])

def fill_all(color):
    """すべてのストリップを指定された色に設定します。"""
    for strip in neo_strips.values():
        strip.fill(tuple(color))
        strip.write()

def clear_all():
    """すべてのストリップを消灯させます。"""
    fill_all([0, 0, 0])


def fade_in_color(strip_name, target_color, duration_ms, stop_flag):
    """
    指定されたストリップを、指定された時間(ms)をかけて、現在の色から目標の色にフェードインさせます。
    
    Args:
        strip_name (str): 対象のNeoPixelストリップの名前 (例: 'LV1')
        target_color (list): 最終的な色 [R, G, B]
        duration_ms (int): フェードインにかける時間（ミリ秒）
        stop_flag (list): [True] になったら停止するフラグ
    """
    current_strip = neo_strips.get(strip_name)
    if not current_strip:
        print(f"Error: NeoPixel strip '{strip_name}' not found for fade_in.")
        return

    # フェードインの開始色を黒 [0, 0, 0] と仮定
    # (より高度な実装では現在の色から始めるべきですが、ここでは単純化)
    start_color = [0, 0, 0]
    
    # 滑らかな変化のためのステップ数とディレイを計算
    steps = 50 # 50段階で変化させる
    if duration_ms < 50: # 短すぎる場合は即座に設定
        delay_ms = 0
    else:
        delay_ms = duration_ms / steps
    
    r_step = (target_color[0] - start_color[0]) / steps
    g_step = (target_color[1] - start_color[1]) / steps
    b_step = (target_color[2] - start_color[2]) / steps
    
    for i in range(1, steps + 1):
        if stop_flag[0]:
            print(f"LED Fade In on {strip_name} stopped by flag.")
            off(strip_name)
            return

        # 中間色の計算
        r = int(start_color[0] + r_step * i)
        g = int(start_color[1] + g_step * i)
        b = int(start_color[2] + b_step * i)
        
        # 値を0-255の範囲にクランプ
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # 色を反映
        current_strip.fill((r, g, b))
        current_strip.write()
        
        if delay_ms > 0:
            time.sleep_ms(int(delay_ms))
        
    # 処理完了後、最終的な色を確実に設定
    current_strip.fill(tuple(target_color))
    current_strip.write()
