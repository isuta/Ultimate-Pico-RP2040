# led_patterns.py
import config
from machine import Pin
import time
from neopixel import NeoPixel

# NeoPixelのインスタンスをグローバル変数として宣言
neopixels = {}

def init_neopixels():
    """
    すべてのNeoPixelストリップを初期化します。
    """
    global neopixels
    for strip_name, strip_info in config.NEOPIXEL_STRIPS.items():
        if strip_info["count"] > 0:
            pin = Pin(strip_info["pin"])
            neopixels[strip_name] = NeoPixel(pin, strip_info["count"])
            print(f"NeoPixel Strip '{strip_name}' on GP{strip_info['pin']} with {strip_info['count']} LEDs initialized.")

def pattern_off(stop_flag_ref):
    """
    すべてのNeoPixelストリップのLEDを消灯します。
    """
    print("全LEDを消灯します")
    for strip in neopixels.values():
        strip.fill((0, 0, 0))
        strip.write()

def pattern_A(stop_flag_ref):
    print("パターンA実行")
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        for i in range(np.n):
            if stop_flag_ref[0]: return
            np[i] = (255, 255, 255)
        np.write()
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
            if stop_flag_ref[0]:
                break
            time.sleep_ms(50)
        for i in range(np.n):
            if stop_flag_ref[0]: return
            np[i] = (0, 0, 0)
        np.write()

def pattern_B(stop_flag_ref):
    print("パターンB実行: 順次点灯（ピンク）")
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        np.fill((0, 0, 0))
        np.write()
        for i in range(np.n):
            if stop_flag_ref[0]: return
            np[i] = (255, 16, 16)
            np.write()
            time.sleep(0.1)
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
            if stop_flag_ref[0]:
                break
            time.sleep_ms(50)
        np.fill((0, 0, 0))
        np.write()

def pattern_C(stop_flag_ref):
    print("パターンC実行: LV1の1番目のLEDを赤に点灯")
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        np.fill((0, 0, 0))
        np.write()
        np[0] = (255, 0, 0)
        np.write()
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
            if stop_flag_ref[0]:
                print("パターンCを中断します。")
                break
            time.sleep_ms(100)
        np.fill((0, 0, 0))
        np.write()

def pattern_D(stop_flag_ref):
    print("パターンD実行: LV1を1秒ごとに順次点灯")
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        np.fill((0, 0, 0))
        np.write()
        for i in range(6):
            if stop_flag_ref[0]:
                break
            time.sleep(1)
            np[i] = (255, 16, 16)
            np.write()
        print("パターンD終了")

# 辞書にパターンを登録
effect_patterns = {
    "A": pattern_A,
    "B": pattern_B,
    "C": pattern_C,
    "D": pattern_D,
    "off": pattern_off,
}
