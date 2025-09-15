# effects.py
import config
import machine
from machine import Pin, UART
import time
import random
from neopixel import NeoPixel

# NeoPixelのインスタンスを格納する辞書
neopixels = {}
# config.pyで定義したすべてのNeoPixelを初期化
for strip_name, strip_info in config.NEOPIXEL_STRIPS.items():
    if strip_info["count"] > 0:
        pin = Pin(strip_info["pin"])
        neopixels[strip_name] = NeoPixel(pin, strip_info["count"])
        print(f"NeoPixel Strip '{strip_name}' on GP{strip_info['pin']} with {strip_info['count']} LEDs initialized.")

# DFPlayerのUARTポート
uart = UART(config.UART_ID, baudrate=config.UART_BAUDRATE, tx=Pin(config.DFPLAYER_TX_PIN), rx=Pin(config.DFPLAYER_RX_PIN))

# DFPlayerの再生コマンド
# 0x0Fコマンドでフォルダ内のファイルを指定
def play_dfplayer_sound(folder_num, file_num):
    print(f"DFPlayer: フォルダ{folder_num}のファイル{file_num}を再生")
    play_sound = bytearray([0x7E, 0xFF, 0x06, 0x0F, 0x00, folder_num, file_num, 0xEF])
    uart.write(play_sound)

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
def playEffectByNum(num):
    """
    指定された番号のコマンドリストを実行します。
    """
    command_list = my_array.get(num)
    if command_list:
        execute_command(command_list)
        return True
    else:
        return False

# 抽選配列を定義
# キー: 抽選番号 (random.choiceで選ばれる番号)
# 値: 実行する処理のタプルのリスト。順に実行される
#
# タプルの形式:
# ('sound', フォルダ番号, ファイル番号) - 指定のMP3を再生
# ('effect', 'エフェクト名')           - effects.py内の関数を実行
# ('delay', 遅延時間[ミリ秒])         - 指定時間待機
my_array = {
    1: [
        ('sound', 2, 1),
    ],
    2: [
        ('sound', 2, 2),
    ],
    3: [
        ('sound', 2, 3),
    ],
    4: [
        ('sound', 2, 4),
    ],
    5: [
        ('sound', 2, 5),
    ],
    6: [
        ('sound', 2, 6),
    ],
    7: [
        ('sound', 2, 7),
    ],
    8: [
        ('sound', 2, 8),
    ],
    9: [
        ('sound', 2, 9),
    ],
    10: [
        ('sound', 2, 10),
    ],
    11: [
        ('sound', 2, 11),
    ],
    12: [
        ('sound', 2, 12),
    ],
    13: [
        ('sound', 2, 13),
    ],
    14: [
        ('sound', 2, 14),
    ],
    15: [
        ('sound', 2, 15),
    ],
    16: [
        ('sound', 2, 16),
    ],
    17: [
        ('sound', 2, 17),
    ],
    18: [
        ('sound', 2, 18),
    ],
    19: [
        ('sound', 2, 19),
    ],
    20: [
        ('sound', 2, 20),
    ],
    21: [
        ('sound', 2, 21),
    ],
    22: [
        ('sound', 2, 22),
    ],
    23: [
        ('sound', 2, 23),
    ],
    24: [
        ('sound', 2, 24),
    ],
    25: [
        ('sound', 2, 25),
    ],
    26: [
        ('sound', 2, 26),
    ],
    27: [
        ('sound', 2, 27),
    ],
    28: [
        ('sound', 2, 28),
    ],
    29: [
        ('sound', 2, 29),
    ],
    30: [
        ('sound', 2, 30),
    ],
    21: [
        ('sound', 2, 31),
    ],
    22: [
        ('sound', 2, 32),
    ],
    23: [
        ('sound', 2, 33),
    ],
    24: [
        ('sound', 2, 34),
    ],
    25: [
        ('sound', 2, 35),
    ],
#    6: [
#        ('sound', 2, 3),
#        ('delay', 3),
#        ('effect', 'B'),
#        ('delay', 60),
#        ('effect', 'F')
#    ],
    #... 拡張していく
}

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
        #time.sleep(3)
        for i in range(np.n):
            np[i] = (0, 0, 0)
        np.write()

# --- 辞書にパターンを登録 (既存) ---
effect_patterns = {
    "A": pattern_A,
    "B": pattern_B,
}

# --- 統合メソッド ---
def playRandomEffect():
    """
    ランダムなエフェクト/サウンドを選び、その抽選番号とコマンドリストを返します。
    """
    # 抽選配列のキーからランダムに選択
    num = random.choice(list(my_array.keys()))

    # 選択されたコマンドリストを取得
    command_list = my_array[num]
    
    # 抽選番号とコマンドリストの両方を返す
    return num, command_list

