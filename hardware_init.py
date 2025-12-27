import time
from machine import Pin, ADC


def init_hardware(config, oled_patterns, neopixel_controller, pwm_led_controller, onboard_led, sound_patterns, servo_rotation_controller, servo_position_controller):
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
    neopixel_controller.init_neopixels()
    if neopixel_controller.is_neopixel_available():
        print(f"NeoPixel: 初期化成功 - 利用可能ストリップ: {list(neopixel_controller.get_available_strips())}")
    else:
        print("NeoPixel: 全ストリップ初期化失敗 - LED機能は無効")

    # PWM LED init
    pwm_led_controller.init_pwm_leds()
    if pwm_led_controller.is_pwm_led_available():
        print(f"PWM LED: 初期化成功 - 利用可能LED: {list(pwm_led_controller.get_available_leds())}")
    else:
        print("PWM LED: 全LED初期化失敗 - PWM LED機能は無効")

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

    # Servo motors - system_init.pyで既に初期化済み（最優先処理）
    # ここでは状態確認のみ
    if servo_rotation_controller.is_servo_available():
        print(f"Servo: 初期化成功 - 利用可能サーボ: {list(servo_rotation_controller.get_available_servos())}")
    else:
        print("Servo: 連続回転型サーボなし")

    if servo_position_controller.is_servo_available():
        print(f"Servo Position: 初期化成功 - 利用可能サーボ: {list(servo_position_controller.get_available_servos())}")
    else:
        print("Servo Position: 角度制御型サーボなし")

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
