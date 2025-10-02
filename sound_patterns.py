# sound_patterns.py
import config
from machine import Pin, UART
import time

# UARTとBUSYピンのインスタンスをグローバル変数として宣言
uart = None
busy_pin = None

def init_dfplayer():
    """
    DFPlayer Miniの初期化処理をすべて実行します。
    UART、BUSYピンの初期化、およびボリューム設定を含みます。
    """
    global uart, busy_pin
    
    # DFPlayerのUARTとBUSYピンの初期化を統合
    uart = UART(config.UART_ID, baudrate=config.UART_BAUDRATE, tx=Pin(config.DFPLAYER_TX_PIN), rx=Pin(config.DFPLAYER_RX_PIN))
    print("DFPlayer UART initialized.")
    
    busy_pin = Pin(config.DFPLAYER_BUSY_PIN, Pin.IN)
    print("DFPlayer BUSY pin initialized.")
    
    time.sleep(1) # 初期化のための待ち時間

    # ボリューム設定を統合 (config.pyから値を読み込むように修正)
    set_volume(config.DFPLAYER_DEFAULT_VOLUME)
    
    # システム起動音を再生
    # システム起動音を直接再生
    startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])
    print("DFPlayer: 起動音を再生")
    if uart:
        uart.write(startup_sound)
    else:
        print("Error: UART not initialized.")
    time.sleep(2)

def play_sound(folder_num, file_num):
    """
    指定されたフォルダと番号のサウンドファイルを再生します。
    """
    print(f"DFPlayer: フォルダ{folder_num}のファイル{file_num}を再生")
    # 0x0Fコマンドでフォルダ内のファイルを指定
    play_command = bytearray([0x7E, 0xFF, 0x06, 0x0F, 0x00, folder_num, file_num, 0xEF])
    if uart:
        uart.write(play_command)
    else:
        print("Error: UART not initialized.")

def set_volume(volume):
    """
    DFPlayerのボリュームを設定します。
    """
    volume_set_command = bytearray([0x7E, 0xFF, 0x06, 0x06, 0x00, 0x00, int(f'0x{volume:02x}', 16), 0xEF])
    if uart:
        uart.write(volume_set_command)
        time.sleep(0.5)

def stop_playback():
    """
    DFPlayerの再生を停止します。
    """
    print("DFPlayer: 再生を停止")
    stop_command = bytearray([0x7E, 0xFF, 0x06, 0x16, 0x00, 0x00, 0x00, 0xEF])
    if uart:
        uart.write(stop_command)
        time.sleep(0.5)