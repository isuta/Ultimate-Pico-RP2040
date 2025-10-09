# oled_patterns.py
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
        # 新しいI2Cバスインスタンスを作成
        i2c = I2C(
            i2c_id, 
            scl=Pin(scl_pin), 
            sda=Pin(sda_pin), 
            freq=i2c_freq
        )
        
        # OLEDディスプレイの初期化 (128x64を想定)
        # アドレス指定がない場合、デフォルトの 0x3C が使用されます
        oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)
        
        # 初期表示 (成功した場合のみ実行)
        oled.fill(0)
        oled.text("OLED Initialized", 0, 0)
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
    
    【修正】: I2Cタイムアウトエラー (Errno 110) に対応するための再試行ロジックを搭載。
    """
    global oled
    if oled is None:
        return

    oled.fill(0)  # 画面をクリア

    line_height = 10 
    
    # 複数行のメッセージを表示
    for i, message in enumerate(message_list[:4]): 
        y_pos = i * line_height 
        x_start = 0 
        oled.text(str(message), x_start, y_pos)
        
    # タイムアウトエラーに対応するための再試行ロジック
    MAX_RETRIES = 1
    for attempt in range(MAX_RETRIES + 1):
        try:
            # 画面に描画を反映
            oled.show()
            if attempt > 0:
                print("OLED: I2C通信が回復し、メッセージを表示しました。")
            return # 成功したら終了
        except OSError as e:
            # Errno 110 (ETIMEDOUT) をチェック
            if '[Errno 110] ETIMEDOUT' in str(e) or '110' in str(e):
                print(f"Warning: OLED I2Cタイムアウトを検出しました (試行 {attempt + 1})。")
                if attempt < MAX_RETRIES:
                    # 再初期化を試みる
                    print("OLED再初期化を試行しています...")
                    # 再初期化の間隔を空けて、I2Cバスの安定を待つ
                    time.sleep_ms(50) 
                    init_oled()
                    if oled is None:
                        print("Error: OLED再初期化に失敗しました。表示を中止します。")
                        return # 再初期化失敗
                    # 再初期化成功。ループの次のイテレーションで再試行。
                else:
                    print("Error: OLED I2Cタイムアウトが再試行後も継続しました。表示を中止します。")
                    return # 最大試行回数を超えた
            else:
                # その他のOSError
                print(f"Error: OLED表示中に予期せぬOSErrorが発生しました: {e}")
                return


def clear_screen():
    """
    OLED画面を完全にクリアします。
    
    【修正】: I2Cタイムアウトエラーに対応するためのエラーハンドリングを搭載。
    """
    global oled
    if oled is None:
        return
    
    oled.fill(0)
    
    # oled.show() でエラーが出る場合があるため、try-except でラップ
    try:
        oled.show()
    except OSError as e:
        if '[Errno 110] ETIMEDOUT' in str(e) or '110' in str(e):
            print("Warning: OLED I2Cタイムアウトを検出しました (クリア時)。showをスキップします。")
        else:
            print(f"Error: OLEDクリア中に予期せぬOSErrorが発生しました: {e}")

# (注意: このコードは init_oled が外部から呼び出されることを前提としています)
