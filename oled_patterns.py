# oled_patterns.py
import config
from machine import I2C, Pin
import ssd1306
import time
import math

# OLEDのインスタンスをグローバル変数として宣言
oled = None

def init_oled():
    """
    OLEDディスプレイを初期化します。
    """
    global oled
    i2c = I2C(config.I2C_ID, sda=Pin(config.OLED_SDA_PIN), scl=Pin(config.OLED_SCL_PIN), freq=config.I2C_FREQ)
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    print("OLED initialized.")

def circle(x, y, l, color):
    """
    円を描画します。
    """
    if oled is None: return
    for r in range(360):
        oled.pixel(int(x + l * math.cos(math.radians(r))), int(y - l * math.sin(math.radians(r))), color)

def cross(x, y, l, color):
    """
    バツ (☓) を描画します。
    """
    if oled is None: return
    for i in range(l):
        oled.pixel(x - i, y - i, color)
        oled.pixel(x + i, y + i, color)
    for i in range(l):
        oled.pixel(x + i, y - i, color)
        oled.pixel(x - i, y + i, color)

def show_display(message, draw_result):
    """
    OLEDにメッセージと結果（円またはバツ）を表示します。
    """
    if oled is None: return
    print(str(message))
    oled.init_display()

    if draw_result == 1:
        circle(9, 43, 5, True)
    elif draw_result == 2:
        cross(9, 43, 5, True)

    oled.fill_rect(20, 40, 30, 10, 0)
    oled.show()
    oled.text(str(message), 20, 40)
    oled.show()

def show_title():
    """
    OLEDの上部にタイトルと枠を表示します。
    """
    if oled is None: return
    oled.init_display()
    oled.rect(10, 0, 100, 18, 1)
    oled.show()
    oled.text("Push Button!", 13, 5)
    oled.show()
