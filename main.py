# main.py
import config
from machine import I2C, Pin, UART
import ssd1306
import time
import random
import math # 数学関数
import effects

# 設定
uart = UART(config.UART_ID, baudrate=config.UART_BAUDRATE, tx=Pin(config.DFPLAYER_TX_PIN), rx=Pin(config.DFPLAYER_RX_PIN))

# シリアルデータの定義
startup_sound = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])
no1_play = bytearray([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xEF])

# OLEDの準備
i2c = I2C(config.I2C_ID, sda=Pin(config.OLED_SDA_PIN), scl=Pin(config.OLED_SCL_PIN), freq=config.I2C_FREQ)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# 入力用のプルダウン抵抗を使用するピンとして設定。
button = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

# 初期待ち
time.sleep(2.0)

# 円描画関数（三角関数を使用）
def circle(x, y, l, color):
    for r in range(360):
        oled.pixel(int(x + l * math.cos(math.radians(r))), int(y - l * math.sin(math.radians(r))), color)

# バツ (☓) 描画関数
def cross(x, y, l, color):
    # 対角線1 (左上から右下へ)
    for i in range(l):
        oled.pixel(x - i, y - i, color)  # 左上から中心
        oled.pixel(x + i, y + i, color)  # 中心から右下

    # 対角線2 (右上から左下へ)
    for i in range(l):
        oled.pixel(x + i, y - i, color)  # 右上から中心
        oled.pixel(x - i, y + i, color)  # 中心から左下

# OLEDにメッセージを表示する
def showDisplay(message, draw_result) :
    print(str(message))
    oled.init_display()

    if draw_result == 1:
        # (x, y, 半径, 色) 円描画関数呼び出し
        circle(9, 43, 5, True)
    elif draw_result == 2:
        # (x, y, 半径, 色) バツ描画関数呼び出し
        cross(9, 43, 5, True)

    oled.fill_rect(20,40,30,10,0)
    oled.show()
    oled.text(str(message),20,40)
    oled.show()

# OLEDの上部に枠と表示する　TODO　そのうち共通化して文字変えられるようにするかも
def showTitle() :
    oled.init_display()
    oled.rect(10,0,100,18,1)
    oled.show()
    oled.text("Push Button!",13,5)
    oled.show()

# DfPlayerの初期化
def initDfplayer() :
    oled.init_display()
    draw_type = 0
    print(draw_type)
    showDisplay('init start', draw_type)
    
    # ボリュームサイズ変更
    volumeSet(15)

    # システム起動音再生
    uart.write(startup_sound)

    showDisplay('init end', draw_type)
    time.sleep(2)  # 2秒待機してから次を再生（必要に応じて調整）

# DfPlayerのボリュームサイズ変更関数
def volumeSet(volume) :
    volume_set = bytearray([0x7E, 0xFF, 0x06, 0x06, 0x00, 0x00, int(f'0x{volume:02x}', 16), 0xEF])

    #　ボリューム設定
    uart.write(volume_set)    
    time.sleep(0.5)  # 少し待機

# 抽選配列からランダムに取得した数値(ファイル番号)を返す
def randomSelect():
    print('first_key:' + str(my_array[0]) + ', first_key:' + str(my_array[-1]))
    num = random.randint(my_array[0], my_array[-1])
    print('select array num ' + str(num))

    return int(num)

# ランダムに曲を再生する
def randomPlay() :
    # 抽選番号と実行するコマンドリストを同時に受け取る
    num, command_list = effects.playRandomEffect()

    # ここで先にOLEDに表示する
    draw_type = 2
    if num == 6 :
        draw_type = 1
    showDisplay('select file ' + str(num), draw_type)
    
    # その後、コマンドリストを実行
    effects.execute_command(command_list)

# 初期化
button_pressed = False
press_time = 0
release_time = 0
selected_scenario = 1
last_press_time = 0  # 最後にボタンが押された時間を記録
initDfplayer()
draw_type = 0
showDisplay('loading now', draw_type)
time.sleep(5)  # 少し待機

# デバッグモード判定
debug_mode = False
if button.value() == 1:
    # 意図しない誤作動を防ぐため、少し待機（チャタリング対策）
    time.sleep(0.05)
    
    start_time = time.ticks_ms()
    # ボタンが押されている間、ループを継続
    while button.value() == 1:
        # 1秒（1000ミリ秒）以上経過したらデバッグモードに移行
        if time.ticks_diff(time.ticks_ms(), start_time) > 1000:
            debug_mode = True
            showDisplay("Debug Mode", draw_type)
            time.sleep(1) # ボタンが離されるのを待つ
            break

# ボタン入力待ちループ
while True:
    if debug_mode:
        current_button_value = button.value()
        current_time = time.ticks_ms()

        # デバウンス処理
        if time.ticks_diff(current_time, last_press_time) < 300:
            continue
        
        # ボタンが押されている場合
        if current_button_value == 1:
            # 押された瞬間を検知
            if not button_pressed:
                button_pressed = True
                press_time = current_time

            # 押下時間が1秒を超えたら長押しと判定し、すぐに実行
            if time.ticks_diff(current_time, press_time) >= 1000:
                print("長押し（実行開始）")
                command_list = effects.my_array.get(selected_scenario)
                if command_list:
                    showDisplay(f"Executing: {selected_scenario}", 0)
                    effects.execute_command(command_list)
                else:
                    showDisplay("Scenario not found", 0)

                # 実行後、ボタンが離されるまで待機
                while button.value() == 1:
                    time.sleep(0.1)
                button_pressed = False
                last_press_time = time.ticks_ms()
                
        # ボタンが離された場合
        else:
            if button_pressed:
                # 短押しとして判定
                press_duration = time.ticks_diff(current_time, press_time)
                if press_duration < 500:
                    print("短押し")
                    selected_scenario += 1
                    if selected_scenario > len(effects.my_array):
                        selected_scenario = 1
                    showDisplay(f"Select: {selected_scenario}", 0)
                
                button_pressed = False
                last_press_time = current_time

    else:
        # 通常の抽選モード用の処理
        if button.value() == 1:
            randomPlay()
            time.sleep(5)
            showTitle()

