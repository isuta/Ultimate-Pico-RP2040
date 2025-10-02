# LED Patterns Module:oled_patterns.py
import config
import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C # MicroPythonのssd1306ライブラリを使用

# OLEDオブジェクト
oled = None

def init_oled():
    """
    OLEDディスプレイを初期化し、グローバル変数 'oled' に設定します。
    """
    global oled
    
    # config.py から設定を直接読み込み
    i2c_id = config.I2C_ID
    scl_pin = config.OLED_SCL_PIN
    sda_pin = config.OLED_SDA_PIN
    i2c_freq = config.I2C_FREQ
    
    # I2Cバスの初期化
    try:
        i2c = I2C(
            i2c_id, 
            scl=Pin(scl_pin), 
            sda=Pin(sda_pin), 
            freq=i2c_freq
        )
        
        # OLEDディスプレイの初期化 (128x64を想定)
        # アドレス指定がない場合、デフォルトの 0x3C が使用されます
        oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)
        
        # 初期表示
        oled.fill(0)
        oled.text("System Ready!", 0, 0)
        oled.text("Welcome.", 0, 16)
        oled.show()
        print("OLEDディスプレイの初期化が完了しました。")
        
    except ValueError as e:
        print(f"I2C初期化エラー: {e}")
        print(f"SCLピン: {scl_pin}, SDAピン: {sda_pin} が正しいか確認してください。")
        oled = None # エラー時はOLEDオブジェクトをNoneにする
    except Exception as e:
        print(f"OLED初期化中に予期せぬエラーが発生しました: {e}")
        oled = None


def push_message(message_list):
    """
    メッセージリストをOLEDに表示します。
    メッセージリストは最大4行分を想定します。
    """
    global oled
    if oled is None:
        return

    # 画面をクリア
    oled.fill(0) 

    # 1行あたりのY座標のオフセット (1行の高さは通常8ピクセル)
    line_height = 10 
    
    for i, message in enumerate(message_list):
        # Y座標を計算 (0, 10, 20, 30...)
        y_pos = i * line_height 
        
        # X座標を画面の左端に固定 (0) 
        # これで文字がはみ出さなくなります。
        x_start = 0 
        
        oled.text(str(message), x_start, y_pos)

    # 画面に描画を反映
    oled.show()


def clear_screen():
    """
    OLED画面を完全にクリアします。
    """
    global oled
    if oled is None:
        return
    
    oled.fill(0)
    oled.show()

# (注意: このコードは init_oled が外部から呼び出されることを前提としています)