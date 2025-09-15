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
    
    # その後、コマンドリストを実行
    effects.execute_command(command_list)
    
    # 抽選した番号を返す
    return num

# 初期化
button_pressed = False
press_time = 0
release_time = 0
selected_scenario = 1
last_press_time = 0  # 最後にボタンが押された時間を記録
debug_mode = False   # デバッグモード判定
current_display = "" # 現在表示されている文字列を保持

# 初期化と表示
initDfplayer()
draw_type = 0
showDisplay('loading now', draw_type)
time.sleep(5)

if button.value() == 1:
    # 意図しない誤作動を防ぐため、少し待機（チャタリング対策）
    time.sleep(0.05)
    
    start_time = time.ticks_ms()
    # ボタンが押されている間、ループを継続
    while button.value() == 1:
        # 1秒（1000ミリ秒）以上経過したらデバッグモードに移行
        if time.ticks_diff(time.ticks_ms(), start_time) > 1000:
            debug_mode = True
            time.sleep(1) # ボタンが離されるのを待つ
            break

# 最初の表示を一度だけ行う
if debug_mode:
    current_display = "Debug Mode"
else:
    current_display = "Press the button"

showDisplay(current_display, 0)

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
                # my_arrayの最初のキーを取得して実行
                first_scenario = list(effects.my_array.keys())[0]
                command_list = effects.my_array.get(first_scenario)

                if effects.playEffectByNum(selected_scenario):
                    new_display = f"Executing: {selected_scenario}"
                    if new_display != current_display:
                        showDisplay(new_display, 0)
                        current_display = new_display
                else:
                    new_display = "Scenario not found"
                    if new_display != current_display:
                        showDisplay(new_display, 0)
                        current_display = new_display

                while button.value() == 1:
                    time.sleep(0.1)
                button_pressed = False
                last_press_time = time.ticks_ms()
                
                new_display = "Debug Mode"
                if new_display != current_display:
                    showDisplay(new_display, 0)
                    current_display = new_display
                
        # ボタンが離された場合
        else:
            if button_pressed:
                press_duration = time.ticks_diff(current_time, press_time)
                if press_duration < 500:
                    print("短押し")
                    selected_scenario += 1
                    if selected_scenario > len(effects.my_array):
                        selected_scenario = 1
                    
                    new_display = f"Select: {selected_scenario}"
                    if new_display != current_display:
                        showDisplay(new_display, 0)
                        current_display = new_display
                
                button_pressed = False
                last_press_time = current_time

    # 通常モードの処理
    else:
        # 通常モード
        new_display = "Press the button"
        if new_display != current_display:
            # このブロックがループで何度も実行されるため、ここに表示ロジックを追加
            showDisplay(new_display, 0)
            current_display = new_display
        
        # 通常の抽選モード用の処理
        if button.value() == 1:
            # 抽選した番号を受け取る
            num = randomPlay()
            
            # 再生したファイル番号を表示
            new_display = f"Now playing: {num}"
            if new_display != current_display:
                showDisplay(new_display, 0)
                current_display = new_display
            
            # 再生が完了するまで待機
            time.sleep(5)
            
            # 待機メッセージに戻る
            new_display = "Press the button"
            if new_display != current_display:
                showDisplay(new_display, 0)
                current_display = new_display

