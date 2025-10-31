import time
from machine import Pin, ADC


def init_hardware(config, oled_patterns, led_patterns, onboard_led, sound_patterns):
    """
    Initialize hardware components and return a dict with important resources/flags.

    Returns keys:
      - button, button_available
      - volume_pot
      - init_messages (list)
      - final_messages (list)
    """
    init_messages = ['Loading...']

    # Button
    try:
        button = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        button_available = True
        print(f"Button initialized on pin {config.BUTTON_PIN}")
    except Exception as e:
        print(f"Warning: Button initialization failed on pin {config.BUTTON_PIN}: {e}")
        print("Button functionality will be disabled. Program will run in console-only mode.")
        button = None
        button_available = False

    # OLED initialization
    try:
        oled_patterns.init_oled()
    except Exception as e:
        # Let oled_patterns itself handle availability, but log if init fails
        print(f"Warning: oled_patterns.init_oled() raised: {e}")

    if oled_patterns.is_oled_available():
        print("OLED: 初期化成功")
    else:
        print("OLED: 初期化失敗 - ディスプレイ機能は無効")
        init_messages.append('OLED: Disabled')

    if button_available:
        print("Button: 初期化成功")
    else:
        print("Button: 初期化失敗 - ボタン機能は無効（コンソールモード）")
        init_messages.append('Console Mode')

    # Show loading message on OLED (if available)
    try:
        oled_patterns.push_message(init_messages)
    except Exception:
        pass

    # NeoPixel init
    led_patterns.init_neopixels()
    if led_patterns.is_neopixel_available():
        print(f"NeoPixel: 初期化成功 - 利用可能ストリップ: {list(led_patterns.get_available_strips())}")
    else:
        print("NeoPixel: 全ストリップ初期化失敗 - LED機能は無効")

    # Onboard LED
    onboard_led.init_onboard_led()
    if onboard_led.is_onboard_led_available():
        print("Onboard LED: 初期化成功")
    else:
        print("Onboard LED: 初期化失敗 - 内蔵LED機能は無効")

    # DFPlayer
    sound_patterns.init_dfplayer()
    if sound_patterns.is_dfplayer_available():
        print("DFPlayer: 初期化成功")
    else:
        print("DFPlayer: 初期化失敗 - 音声機能は無効")

    print("=====================================")
    # small wait for DFPlayer to settle if present
    time.sleep(1)

    # ADC / Potentiometer
    try:
        volume_pot = ADC(Pin(config.POTENTIOMETER_PIN))
    except Exception as e:
        print(f"Error initializing ADC on pin {config.POTENTIOMETER_PIN}: {e}")
        volume_pot = None

    # Construct final messages (main may append console mode later)
    final_messages = []
    # We'll leave final_messages population to caller depending on which components are used.

    return {
        'button': button,
        'button_available': button_available,
        'volume_pot': volume_pot,
        'init_messages': init_messages,
        'final_messages': final_messages,
    }
