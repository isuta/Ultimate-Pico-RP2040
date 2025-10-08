import config
from machine import Pin
import time
from neopixel import NeoPixel

# NeoPixelのインスタンスを格納する辞書
neopixels = {}

# すべてのストリップを結合したときのLEDの総数
total_led_count = 0
# グローバルインデックスから (strip_instance, local_index) を検索するためのリスト
global_led_map = [] 
# 全LEDの現在の色を保持するキャッシュ (R, G, B)
led_color_cache = []

def init_neopixels():
    """
    config.py で定義されたすべての NeoPixel ストリップを初期化し、
    グローバルインデックスマッピングを作成します。
    """
    global neopixels, total_led_count, global_led_map, led_color_cache
    
    total_led_count = 0
    global_led_map = []
    
    # ストリップ名でソートして初期化順序を保証 (configの定義順)
    sorted_strips = sorted(config.NEOPIXEL_STRIPS.items())
    
    for strip_name, strip_info in sorted_strips:
        count = strip_info["count"]
        if count > 0:
            pin = Pin(strip_info["pin"])
            np = NeoPixel(pin, count)
            neopixels[strip_name] = np
            print(f"NeoPixel Strip '{strip_name}' on GP{strip_info['pin']} with {count} LEDs initialized.")
            
            # グローバルインデックスマッピングを作成
            for i in range(count):
                # (NeoPixelインスタンス, そのストリップ内でのローカルインデックス) を保存
                global_led_map.append((np, i))
                
            total_led_count += count
    
    # 色キャッシュの初期化
    led_color_cache = [(0, 0, 0)] * total_led_count
    
    print(f"Total LEDs initialized: {total_led_count}")


def set_global_led(index, r, g, b):
    """
    グローバルインデックス (0から total_led_count - 1) を使用して、単一のLEDの色を設定します。
    """
    global led_color_cache
    if 0 <= index < total_led_count:
        np, local_index = global_led_map[index]
        
        # 色を設定
        np[local_index] = (r, g, b)
        
        # キャッシュを更新
        led_color_cache[index] = (r, g, b)
        
        # np.write() は呼び出しません。呼び出し元でまとめて実行します。
        return True
    return False

def set_global_leds_by_indices(indices, r, g, b):
    """
    複数のグローバルインデックスを指定して、単一の色を一括で設定し、書き込みます。
    """
    modified_strips = set()
    for index in indices:
        if set_global_led(index, r, g, b):
            # 変更があったストリップインスタンスを記録
            modified_strips.add(global_led_map[index][0])
            
    # 変更があったストリップのみを書き込み
    for np in modified_strips:
        np.write()
        
# --- NEW: フェード機能 ---

def fade_global_leds(indices, start_color, end_color, duration_ms, stop_flag_ref):
    """
    指定されたグローバルインデックスのLED群を、開始色から終了色まで指定時間でフェードさせます。
    """
    if not indices or duration_ms <= 0:
        return

    # フェードの滑らかさを決めるインターバル (ここでは 10ms ごとに更新)
    STEP_INTERVAL_MS = 10
    
    # 全体のステップ数を計算
    num_steps = duration_ms // STEP_INTERVAL_MS
    if num_steps == 0:
        # 1ステップで終了色に設定
        set_global_leds_by_indices(indices, end_color[0], end_color[1], end_color[2])
        return
        
    # RGB 各チャンネルの総変化量
    delta_r = end_color[0] - start_color[0]
    delta_g = end_color[1] - start_color[1]
    delta_b = end_color[2] - start_color[2]
    
    # 1ステップあたりの変化量 (浮動小数点数で保持)
    step_r = delta_r / num_steps
    step_g = delta_g / num_steps
    step_b = delta_b / num_steps
    
    print(f"LED: フェード開始 ({duration_ms}ms, {num_steps}ステップ)")
    
    current_r, current_g, current_b = start_color
    
    # フェード実行
    for step in range(num_steps):
        if stop_flag_ref[0]:
            print("フェードパターンを中断しました。")
            break
            
        # 現在の色を更新（浮動小数点数を加算）
        current_r += step_r
        current_g += step_g
        current_b += step_b
        
        # 整数に変換し、0-255 の範囲にクリップ
        r = max(0, min(255, int(current_r)))
        g = max(0, min(255, int(current_g)))
        b = max(0, min(255, int(current_b)))
        
        # LEDに色を適用
        modified_strips = set()
        for index in indices:
            if set_global_led(index, r, g, b):
                modified_strips.add(global_led_map[index][0])
                
        # 画面に書き込み
        for np in modified_strips:
            np.write()
            
        time.sleep_ms(STEP_INTERVAL_MS)

    # 確実に終了色に設定する（最後のステップの計算誤差を解消）
    if not stop_flag_ref[0]:
        set_global_leds_by_indices(indices, end_color[0], end_color[1], end_color[2])


def get_total_led_count():
    """
    初期化された全LEDの総数を返します。
    """
    return total_led_count

def execute_color_command(strip_name, led_index, r, g, b, duration_ms, stop_flag_ref):
    """
    （従来の関数）指定されたストリップ上のLEDを指定された時間点灯させる。
    """
    if strip_name not in neopixels:
        print(f"Error: Strip '{strip_name}' は初期化されていません。")
        return

    np = neopixels[strip_name]
    
    # ストリップの開始グローバルインデックスを特定
    start_global_index = -1
    current_index = 0
    for name, info in sorted(config.NEOPIXEL_STRIPS.items()):
        if name == strip_name:
            start_global_index = current_index
            break
        current_index += info['count']
    
    original_colors = []
    indices_to_restore = []

    # 1. 色の設定
    if led_index == "ALL":
        print(f"LED: ストリップ '{strip_name}' のすべてを ({r}, {g}, {b}) で点灯")
        for i in range(np.n):
            original_colors.append(np[i]) 
            np[i] = (r, g, b)
            indices_to_restore.append(start_global_index + i)
        np.write()
    else:
        try:
            index = int(led_index)
            if 0 <= index < np.n:
                print(f"LED: ストリップ '{strip_name}' インデックス {index} を ({r}, {g}, {b}) で点灯")
                original_colors.append(np[index])
                np[index] = (r, g, b)
                np.write()
                indices_to_restore.append(start_global_index + index)
            else:
                print(f"Error: ストリップ '{strip_name}' の無効なLEDインデックス {index}")
                return
        except ValueError:
            print(f"Error: 無効なLEDインデックス型: {led_index}")
            return

    # 2. 停止フラグをチェックしながら待機
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        if stop_flag_ref[0]:
            print(f"LEDパターンを中断しました: {strip_name}")
            break
        time.sleep_ms(50)
        
    # 3. 元の色に戻します（グローバルキャッシュを利用して復元）
    if indices_to_restore:
        modified_strips = set()
        for i, global_index in enumerate(indices_to_restore):
            if 0 <= global_index < total_led_count:
                # 復元する色は一時設定前の色に戻します
                restore_r, restore_g, restore_b = original_colors[i] 
                
                np_restore, local_index_restore = global_led_map[global_index]
                
                np_restore[local_index_restore] = (restore_r, restore_g, restore_b)
                led_color_cache[global_index] = (restore_r, restore_g, restore_b) # キャッシュも更新
                modified_strips.add(np_restore)
            
        for np in modified_strips:
            np.write()


def pattern_off(stop_flag_ref):
    """
    すべての NeoPixel ストリップのすべての LED を消灯します。
    色キャッシュもリセットされます。
    """
    global led_color_cache
    print("全LEDを消灯します")
    for strip in neopixels.values():
        strip.fill((0, 0, 0))
        strip.write()
        
    # キャッシュをクリア
    led_color_cache = [(0, 0, 0)] * total_led_count
