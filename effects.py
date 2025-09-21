# effects.py
import config
import machine
from machine import Pin, UART
import time
import random
from neopixel import NeoPixel

# グローバル変数として宣言
neopixels = {}
uart = None

# 初期化関数を定義
def init():
    """
    すべてのハードウェア（NeoPixel, DFPlayer）を初期化します。
    この関数は、main.pyから一度だけ呼び出されるべきです。
    """
    global neopixels, uart

    # NeoPixelのインスタンスを初期化し、辞書に格納
    for strip_name, strip_info in config.NEOPIXEL_STRIPS.items():
        if strip_info["count"] > 0:
            pin = Pin(strip_info["pin"])
            neopixels[strip_name] = NeoPixel(pin, strip_info["count"])
            print(f"NeoPixel Strip '{strip_name}' on GP{strip_info['pin']} with {strip_info['count']} LEDs initialized.")

    # DFPlayerのUARTポートを初期化
    uart = UART(config.UART_ID, baudrate=config.UART_BAUDRATE, tx=Pin(config.DFPLAYER_TX_PIN), rx=Pin(config.DFPLAYER_RX_PIN))
    print("DFPlayer UART initialized.")

# DFPlayerの再生コマンド
# 0x0Fコマンドでフォルダ内のファイルを指定
def play_dfplayer_sound(folder_num, file_num):
    print(f"DFPlayer: フォルダ{folder_num}のファイル{file_num}を再生")
    play_sound = bytearray([0x7E, 0xFF, 0x06, 0x0F, 0x00, folder_num, file_num, 0xEF])
    if uart:
        uart.write(play_sound)
    else:
        print("Error: UART not initialized.")

# 停止フラグを引数として受け取るように変更
def execute_command(command_list, stop_flag_ref):
    for cmd in command_list:
        if stop_flag_ref[0]:  # リストの参照をチェック
            print("停止フラグが検出されました。コマンドを中断します。")
            stop_flag_ref[0] = False  # フラグをリセット
            return

        cmd_type = cmd[0]
        
        if cmd_type == 'sound':
            folder_num = cmd[1]
            file_num = cmd[2]
            play_dfplayer_sound(folder_num, file_num)
        elif cmd_type == 'effect':
            pattern_name = cmd[1]
            if pattern_name in effect_patterns:
                # 停止フラグを各パターン関数に渡す
                effect_patterns[pattern_name](stop_flag_ref)
        elif cmd_type == 'delay':
            delay_time = cmd[1]
            # 停止フラグをチェックしながら待機
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < delay_time:
                if stop_flag_ref[0]:
                    print("Delayを中断します。")
                    stop_flag_ref[0] = False
                    return
                time.sleep_ms(50) # 短い間隔でチェック
        else:
            print(f"不明なコマンドタイプ: {cmd_type}")

# デバッグモード用に、指定した番号のエフェクトを実行する関数
def playEffectByNum(scenarios_data, num, stop_flag_ref):
    """
    指定された番号のコマンドリストを実行します。
    """
    command_list = scenarios_data.get(num)
    if command_list:
        execute_command(command_list, stop_flag_ref)
        return True
    else:
        return False

# --- 各パターン関数にも停止フラグの引数を追加 ---
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
        
        # 全LEDを一度消灯する
        np.fill((0, 0, 0))
        np.write()
        
        # 手前から順にピンク色に点灯
        for i in range(np.n):
            if stop_flag_ref[0]: return
            np[i] = (255, 16, 16)
            np.write()
            time.sleep(0.1)
        
        # 3秒待機後、全LEDを消灯する
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
        # 全LEDを消灯
        np.fill((0, 0, 0))
        # 1番目（インデックス0）のLEDを赤に設定
        np[0] = (255, 0, 0)
        np.write()
        # 停止フラグをチェックしながら待機
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
            if stop_flag_ref[0]:
                print("パターンCを中断します。")
                break
            time.sleep_ms(100) # 100msごとにチェック
        # 全LEDを消灯
        np.fill((0, 0, 0))
        np.write()

# --- 辞書にパターンを登録 ---
effect_patterns = {
    "A": pattern_A,
    "B": pattern_B,
    "C": pattern_C, # この行が重要です！
}
