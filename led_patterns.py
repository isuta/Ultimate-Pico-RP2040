import config
from machine import Pin
import time
from neopixel import NeoPixel

# NeoPixelのインスタンスを格納する辞書
neopixels = {}

def init_neopixels():
    """
    config.py で定義されたすべての NeoPixel ストリップを初期化します。
    """
    global neopixels
    for strip_name, strip_info in config.NEOPIXEL_STRIPS.items():
        if strip_info["count"] > 0:
            pin = Pin(strip_info["pin"])
            neopixels[strip_name] = NeoPixel(pin, strip_info["count"])
            print(f"NeoPixel Strip '{strip_name}' on GP{strip_info['pin']} with {strip_info['count']} LEDs initialized.")

def execute_color_command(strip_name, led_index, r, g, b, duration_ms, stop_flag_ref):
    """
    指定されたストリップ上の指定されたLEDを、指定された色で指定された時間点灯させ、
    その後、元の色に戻します。
    """
    if strip_name not in neopixels:
        print(f"Error: Strip '{strip_name}' は初期化されていません。")
        return

    np = neopixels[strip_name]
    
    # 既存の色をバックアップします (継続時間経過後に元の色に戻すため)
    original_colors = []
    
    # LEDを点灯させます
    if led_index == "ALL":
        print(f"LED: ストリップ '{strip_name}' のすべてを ({r}, {g}, {b}) で点灯")
        
        # すべてのLEDの色を保存し、新しい色を設定
        for i in range(np.n):
            original_colors.append(np[i]) 
            np[i] = (r, g, b)
        np.write()
    else:
        try:
            index = int(led_index)
            if 0 <= index < np.n:
                print(f"LED: ストリップ '{strip_name}' インデックス {index} を ({r}, {g}, {b}) で点灯")
                
                # 特定のLEDの色を保存し、新しい色を設定
                original_colors.append(np[index])
                np[index] = (r, g, b)
                np.write()
            else:
                print(f"Error: ストリップ '{strip_name}' の無効なLEDインデックス {index}")
                return
        except ValueError:
            print(f"Error: 無効なLEDインデックス型: {led_index}")
            return

    # 停止フラグをチェックしながら待機します
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        if stop_flag_ref[0]:
            print(f"LEDパターンを中断しました: {strip_name}")
            break
        time.sleep_ms(50)
        
    # 元の色に戻します
    if led_index == "ALL":
        for i in range(np.n):
            np[i] = original_colors[i]
    else:
        try:
            index = int(led_index)
            if 0 <= index < np.n:
                # 保存された単一の色から元の色を復元
                np[index] = original_colors[0] 
        except ValueError:
            pass # led_index が無効だった場合はエラーを無視
            
    np.write()

def pattern_off(stop_flag_ref):
    """
    すべての NeoPixel ストリップのすべての LED を消灯します。
    """
    print("全LEDを消灯します")
    for strip in neopixels.values():
        strip.fill((0, 0, 0))
        strip.write()
