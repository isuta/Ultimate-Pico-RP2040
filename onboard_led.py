# onboard_led.py
import config
from machine import Pin
import time

# 内蔵LEDのインスタンス
onboard_led = None
led_available = False

def init_onboard_led():
    """
    Raspberry Pi Pico 2Wの内蔵LEDを初期化します。
    """
    global onboard_led, led_available
    
    led_available = False
    
    try:
        # Pico 2Wの内蔵LEDを初期化
        onboard_led = Pin(config.ONBOARD_LED_PIN, Pin.OUT)
        onboard_led.off()  # 初期状態は消灯
        print("Onboard LED initialized successfully.")
        led_available = True
        
        # 初期化成功の合図として短時間点滅
        for _ in range(3):
            onboard_led.on()
            time.sleep_ms(100)
            onboard_led.off()
            time.sleep_ms(100)
            
    except Exception as e:
        print(f"Warning: Onboard LED initialization failed: {e}")
        print("Onboard LED functionality will be disabled.")
        onboard_led = None
        led_available = False

def is_onboard_led_available():
    """
    内蔵LEDが利用可能かどうかを返します。
    """
    return led_available

def turn_on():
    """
    内蔵LEDを点灯します。
    """
    if led_available and onboard_led:
        onboard_led.on()

def turn_off():
    """
    内蔵LEDを消灯します。
    """
    if led_available and onboard_led:
        onboard_led.off()

def blink(times=1, on_time_ms=500, off_time_ms=500):
    """
    内蔵LEDを指定回数点滅させます。
    """
    if not led_available or not onboard_led:
        return
        
    for _ in range(times):
        onboard_led.on()
        time.sleep_ms(on_time_ms)
        onboard_led.off()
        if _ < times - 1:  # 最後の点滅の後は待機しない
            time.sleep_ms(off_time_ms)

def set_state(state):
    """
    内蔵LEDの状態を設定します。
    """
    if not led_available or not onboard_led:
        return
        
    if state:
        onboard_led.on()
    else:
        onboard_led.off()
