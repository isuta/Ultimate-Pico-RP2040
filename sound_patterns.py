import config
from machine import Pin, UART
import time

# UARTとBUSYピンのインスタンスをグローバル変数として宣言
uart = None
busy_pin = None

def init_dfplayer():
    """
    DFPlayer Miniの初期化処理をすべて実行します。
    UART、およびDFPlayerの初期化を含みます。
    注: ボリューム設定は main.py のADC処理で行われますが、ここでは最低限のUART初期化を行います。
    """
    global uart, busy_pin
    
    # DFPlayerのUART初期化
    # config.py の最新の定数名 (UART_ID, UART_BAUDRATE) に合わせて修正
    try:
        uart = UART(config.UART_ID, baudrate=config.UART_BAUDRATE, 
                    tx=Pin(config.DFPLAYER_TX_PIN), rx=Pin(config.DFPLAYER_RX_PIN))
        print("DFPlayer UART initialized.")
    except Exception as e:
        # 初期化エラーの詳細を表示
        print(f"Error initializing DFPlayer UART: {e}")
        uart = None # 初期化失敗時はNoneにしておく

    # BUSYピンは config.py で定義されていれば初期化するが、今回はスキップされている可能性を考慮
    # if hasattr(config, 'DFPLAYER_BUSY_PIN'):
    #     try:
    #         busy_pin = Pin(config.DFPLAYER_BUSY_PIN, Pin.IN)
    #         print("DFPlayer BUSY pin initialized.")
    #     except Exception as e:
    #         print(f"Error initializing DFPlayer BUSY pin: {e}")
    #         busy_pin = None
    
    time.sleep(1) # 初期化のための待ち時間

    # システム起動音を再生 (0x03 コマンド: 再生指定曲)
    startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])
    print("DFPlayer: 起動音を再生 (Track 1)")
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
    ボリュームは 0 (ミュート) から 30 (最大) の整数値を取ります。
    """
    # volumeを整数にキャストして0-30の範囲にクリップ (main.pyでクリップ済みだが安全のため)
    volume_byte = max(0, min(int(volume), 30))
    
    # コマンド: 0x06 (ボリューム設定)
    volume_set_command = bytearray([0x7E, 0xFF, 0x06, 0x06, 0x00, 0x00, volume_byte, 0xEF])
    if uart:
        uart.write(volume_set_command)
        # ボリューム設定コマンドの送信後は、DFPlayerがコマンドを処理するのを少し待つ
        time.sleep(0.01) # 以前の0.5秒は長すぎるため、0.01秒に変更を推奨
    else:
        print(f"Error: UART not initialized. Cannot set volume to {volume_byte}.")

def stop_playback():
    """
    DFPlayerの再生を停止します。
    """
    print("DFPlayer: 再生を停止")
    stop_command = bytearray([0x7E, 0xFF, 0x06, 0x16, 0x00, 0x00, 0x00, 0xEF])
    if uart:
        uart.write(stop_command)
        time.sleep(0.01) # 以前の0.5秒は長すぎるため、0.01秒に変更を推奨
    else:
        print("Error: UART not initialized.")
