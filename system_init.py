# system_init.py
from machine import Pin, ADC
import time
import json
import random

import config                # ← ここで直接読み込む
import hardware_init
import sound_patterns
import effects
import oled_patterns
import led_patterns
import onboard_led
import volume_control
import display_manager


def load_scenarios(filename):
    """JSONファイルを読み込んでシナリオデータを整形して返す"""
    with open(filename, 'r') as f:
        scenarios = json.load(f)

    selectable_keys = []
    random_keys = []
    filtered = {}

    for k, v in scenarios.items():
        if not isinstance(k, str) or not k:
            continue
        is_digit_like = k.isdigit() or (k.lstrip('_').isdigit() and k.startswith('_'))
        filtered[k] = v
        selectable_keys.append(k)
        if is_digit_like:
            random_keys.append(k)

    return filtered, sorted(selectable_keys), random_keys


def initialize_system():
    """全ハードと設定を初期化して辞書として返す"""

    print("=== System Initialization Start ===")
    time.sleep(0.5)

    # ---- 各種パラメータ ----
    IDLE_TIMEOUT_MS = getattr(config, 'IDLE_TIMEOUT_MS', 300000)
    POLLING_DELAY_MS = getattr(config, 'MAIN_LOOP_POLLING_MS', 10)
    AUTO_PLAY_INTERVAL_MS = getattr(config, 'AUTO_PLAY_INTERVAL_SECONDS', 60) * 1000

    # ---- シナリオ読み込み ----
    try:
        scenarios_data, valid_scenarios, random_scenarios = load_scenarios('scenarios.json')
        if not scenarios_data:
            raise Exception("scenarios.json is empty or invalid.")
    except Exception as e:
        print(f"[Warning] Scenario load failed: {e}")
        scenarios_data = {
            "1": [["delay", 1000], {"type": "led", "command": "fill", "color": [255, 0, 0], "duration": 1000}],
            "2": [["sound", 1, 1], ["delay", 2000]]
        }
        valid_scenarios = ["1", "2"]
        random_scenarios = ["1", "2"]
        fallback = True
    else:
        fallback = False

    # ---- ハードウェア初期化 ----
    hw = hardware_init.init_hardware(config, oled_patterns, led_patterns, onboard_led, sound_patterns)
    button = hw.get('button')
    button_available = hw.get('button_available', False)
    volume_pot = hw.get('volume_pot')
    init_messages = hw.get('init_messages', [])
    final_messages = hw.get('final_messages', [])

    dm = display_manager.DisplayManager(oled_patterns)

    # ---- ボリューム初期化 ----
    vc = volume_control.PollingVolumeController(volume_pot, sound_patterns, oled_patterns, config)
    initial_volume = vc.init_initial_volume()
    current_volume = None

    if volume_pot and initial_volume is not None and sound_patterns.is_dfplayer_available():
        current_volume = initial_volume
        print(f"Initial volume: {current_volume}")
        final_messages += [f"Vol:{current_volume}", "Init End"]
    elif volume_pot and not sound_patterns.is_dfplayer_available():
        print("Volume pot OK, DFPlayer missing.")
        final_messages += ["No Audio", "Init End"]
    elif not volume_pot and sound_patterns.is_dfplayer_available():
        print("DFPlayer OK, no volume pot.")
        final_messages += ["Audio:OK", "No VolCtrl", "Init End"]
    else:
        final_messages += ["No Audio", "Init End"]

    if not button_available:
        final_messages = ["Console Mode"] + final_messages

    dm.push_message(final_messages)

    # ---- コンソール表示 ----
    print("\n=== Hardware Summary ===")
    print(f"Button: {'OK' if button_available else 'N/A'}")
    print(f"OLED: {'OK' if oled_patterns.is_oled_available() else 'N/A'}")
    print(f"Audio: {'OK' if sound_patterns.is_dfplayer_available() else 'N/A'}")
    print(f"LED: {'OK' if led_patterns.is_neopixel_available() else 'N/A'}")
    print(f"Volume Pot: {'OK' if volume_pot else 'N/A'}")
    print("=========================")

    # ---- LEDで完了表示 ----
    if onboard_led.is_onboard_led_available():
        onboard_led.blink(times=2, on_time_ms=300, off_time_ms=200)

    # ---- 初期化情報を返却 ----
    return {
        "config": config,
        "display": dm,
        "volume_controller": vc,
        "current_volume": current_volume,
        "button": button,
        "button_available": button_available,
        "volume_pot": volume_pot,
        "scenarios": scenarios_data,
        "valid_scenarios": valid_scenarios,
        "random_scenarios": random_scenarios,
        "timeouts": {
            "idle": IDLE_TIMEOUT_MS,
            "polling": POLLING_DELAY_MS,
            "autoplay": AUTO_PLAY_INTERVAL_MS
        },
        "fallback": fallback
    }
