import board
import digitalio

# GPIO20をLED出力ピンとして設定
led = digitalio.DigitalInOut(board.GP20)
led.direction = digitalio.Direction.OUTPUT

# GPIO18をボタン入力ピンとして設定
button = digitalio.DigitalInOut(board.GP18)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP  # 内部プルアップ抵抗を有効化

while True:
    if not button.value:  # ボタンが押されているとき（LOWになる）
        led.value = True  # LEDを点灯
    else:
        led.value = False  # LEDを消灯
