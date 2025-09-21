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

def execute_command(command_list):
    for cmd in command_list:
        cmd_type = cmd[0] # タプルの最初の要素でタイプを判断
        
        if cmd_type == 'sound':
            folder_num = cmd[1]
            file_num = cmd[2]
            play_dfplayer_sound(folder_num, file_num)
        elif cmd_type == 'effect':
            pattern_name = cmd[1]
            if pattern_name in effect_patterns:
                effect_patterns[pattern_name]()
        elif cmd_type == 'delay':
            delay_time = cmd[1]
            time.sleep_ms(delay_time)
        else:
            print(f"不明なコマンドタイプ: {cmd_type}")

# デバッグモード用に、指定した番号のエフェクトを実行する関数
def playEffectByNum(scenarios_data, num):
    """
    指定された番号のコマンドリストを実行します。
    """
    command_list = scenarios_data.get(num)
    if command_list:
        execute_command(command_list)
        return True
    else:
        return False

# --- パターンごとのメソッドを定義 (既存) ---
def pattern_A():
    # 例: 白色点灯・消灯
    print("パターンA実行")
    # ここでは仮にLV1を使用
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        for i in range(np.n):
            np[i] = (255, 255, 255)
        np.write()
        time.sleep(3)
        for i in range(np.n):
            np[i] = (0, 0, 0)
        np.write()

def pattern_B():
    # 6個のLEDを手前から順にピンク色に点灯するパターン
    print("パターンB実行: 順次点灯（ピンク）")
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        
        # 全LEDを一度消灯する
        for i in range(np.n):
            np[i] = (0, 0, 0)
        np.write()
        
        # 手前から順にピンク色に点灯
        for i in range(np.n):
            np[i] = (255, 16, 16)  # ピンク色 (RGB値)
            np.write()
            time.sleep(0.1)  # 0.1秒待機
        
        # 3秒待機後、全LEDを消灯する
        for i in range(np.n):
            np[i] = (0, 0, 0)
        np.write()

def pattern_C():
    # LV1の1つ目のLEDを赤色に点灯させる
    print("パターンC実行: LV1の1番目のLEDを赤に点灯")
    if "LV1" in neopixels:
        np = neopixels["LV1"]
        # 全LEDを消灯
        np.fill((0, 0, 0))
        # 1番目（インデックス0）のLEDを赤に設定
        np[0] = (255, 0, 0)
        np.write()
        # 3秒待機
        time.sleep(3)
        # 全LEDを消灯
        np.fill((0, 0, 0))
        np.write()

# --- 辞書にパターンを登録 (既存) ---
effect_patterns = {
    "A": pattern_A,
    "B": pattern_B,
}

# --- 統合メソッド ---
def playRandomEffect(scenarios_data):
    if not scenarios_data:
        return None, None

    """
    ランダムなエフェクト/サウンドを選び、その抽選番号とコマンドリストを返します。
    """
    # 抽選配列のキーからランダムに選択
    num = random.choice(list(scenarios_data.keys()))
    command_list = scenarios_data[num]

    # 抽選番号とコマンドリストの両方を返す
    return num, command_list