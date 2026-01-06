# system_init.py
from machine import Pin, ADC
import time
import json
import random

import config              # ← configモジュールをインポート済み
import logger              # ログ出力

# Wi-Fi制御（CYW43のログメッセージ抑制）
if not config.WIFI_ENABLED:
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
    except Exception as e:
        logger.log_warning(f"Wi-Fi disable failed: {e}")

import hardware_init
import sound_patterns      # ← DFPlayerのインスタンス（dfplayer）を持つことが期待されるモジュール
import effects             # ← ステッピングモーターのインスタンス（motor）を持つことが期待されるモジュール
import oled_patterns
import neopixel_controller
import pwm_led_controller
import onboard_led
import servo_rotation_controller
import servo_position_controller
import volume_control
import display_manager


def load_scenarios(filename):
    """JSONファイルを読み込んでシナリオデータを整形して返す"""
    try:
        with open(filename, 'r') as f:
            scenarios = json.load(f)
    except OSError as e:
        logger.log_error(f"Cannot open {filename}: {e}")
        raise
    except ValueError as e:
        logger.log_error(f"Invalid JSON format in {filename}: {e}")
        raise
    except Exception as e:
        logger.log_error(f"Failed to load scenarios: {e}")
        import sys
        sys.print_exception(e)
        raise

    try:
        selectable_keys = []
        random_keys = []
        filtered = {}

        for k, v in scenarios.items():
            if not isinstance(k, str) or not k:
                logger.log_warning(f"Invalid scenario key: {k}")
                continue
            is_digit_like = k.isdigit() or (k.lstrip('_').isdigit() and k.startswith('_'))
            filtered[k] = v
            selectable_keys.append(k)
            if is_digit_like:
                random_keys.append(k)

        if not filtered:
            raise ValueError("No valid scenarios found in JSON file")

        return filtered, sorted(selectable_keys), random_keys
    except Exception as e:
        logger.log_error(f"Failed to process scenario data: {e}")
        import sys
        sys.print_exception(e)
        raise


def initialize_system():
    """全ハードと設定を初期化して辞書として返す"""
    
    # ---------------------------------------------------------------------
    # ★ サーボモーター即座停止（最優先処理）
    # ---------------------------------------------------------------------
    # システム起動直後、サーボがフローティング状態で回転している場合があるため
    # 他の処理より前にPWM信号をオフにして完全停止させる
    try:
        servo_rotation_controller.init_servos()
        servo_position_controller.init_servos()
    except Exception:
        pass  # エラーは無視して続行（hardware_initで再初期化される）
    # ---------------------------------------------------------------------

    logger.log_info("=== System Initialization Start ===")
    time.sleep(0.5)

    # ---------------------------------------------------------------------
    # ★ モジュール初期化 (グローバル/シングルトンインスタンスの生成)
    # ---------------------------------------------------------------------
    try:
        # 1. Motor (effectsモジュール) の初期化
        effects.init()
        logger.log_info("Motor (effects) module initialized.")
    except Exception as e:
        logger.log_warning(f"Motor (effects) initialization failed (Continuing): {e}")

    try:
        # 2. Sound Patterns (DFPlayer) の初期化
        # configモジュールを参照してDFPlayerをセットアップすることを想定
        sound_patterns.init(config)
        logger.log_info("Sound patterns (DFPlayer) module initialized.")
    except Exception as e:
        logger.log_warning(f"Sound patterns initialization failed (DFPlayer not available): {e}")
    # ---------------------------------------------------------------------

    # ---- 各種パラメータ ----
    IDLE_TIMEOUT_MS = getattr(config, 'IDLE_TIMEOUT_MS', 300000)
    POLLING_DELAY_MS = getattr(config, 'MAIN_LOOP_POLLING_MS', 10)
    AUTO_PLAY_INTERVAL_MS = getattr(config, 'AUTO_PLAY_INTERVAL_SECONDS', 60) * 1000

    # ---- シナリオ読み込み ----
    try:
        scenarios_data, valid_scenarios, random_scenarios = load_scenarios('scenarios.json')
        if not scenarios_data:
            raise ValueError("scenarios.json is empty or invalid.")
        fallback = False
        logger.log_info(f"Loaded {len(scenarios_data)} scenarios")
    except OSError as e:
        logger.log_error(f"Cannot read scenarios.json: {e}")
        logger.log_warning("Using fallback scenarios...")
        scenarios_data = {
            "1": [["delay", 1000], {"type": "led", "command": "fill", "color": [255, 0, 0], "duration": 1000}],
            "2": [["sound", 1, 1], ["delay", 2000]]
        }
        valid_scenarios = ["1", "2"]
        random_scenarios = ["1", "2"]
        fallback = True
    except ValueError as e:
        logger.log_error(f"Invalid scenario format: {e}")
        logger.log_warning("Using fallback scenarios...")
        scenarios_data = {
            "1": [["delay", 1000], {"type": "led", "command": "fill", "color": [255, 0, 0], "duration": 1000}],
            "2": [["sound", 1, 1], ["delay", 2000]]
        }
        valid_scenarios = ["1", "2"]
        random_scenarios = ["1", "2"]
        fallback = True
    except Exception as e:
        logger.log_error(f"Scenario load failed: {e}")
        import sys
        sys.print_exception(e)
        logger.log_warning("Using fallback scenarios...")
        scenarios_data = {
            "1": [["delay", 1000], {"type": "led", "command": "fill", "color": [255, 0, 0], "duration": 1000}],
            "2": [["sound", 1, 1], ["delay", 2000]]
        }
        valid_scenarios = ["1", "2"]
        random_scenarios = ["1", "2"]
        fallback = True

    # ---- ハードウェア初期化 ----
    # hardware_init.pyは、DFPlayer以外の個別のHW初期化を担当していると想定
    try:
        hw = hardware_init.init_hardware(config, oled_patterns, neopixel_controller, pwm_led_controller, onboard_led, sound_patterns, servo_rotation_controller, servo_position_controller)
        button = hw.get('button')
        button_available = hw.get('button_available', False)
        volume_pot = hw.get('volume_pot')
        init_messages = hw.get('init_messages', [])
        final_messages = hw.get('final_messages', [])
    except OSError as e:
        logger.log_error(f"Hardware initialization failed: {e}")
        import sys
        sys.print_exception(e)
        # 最小限の構成で続行
        button = None
        button_available = False
        volume_pot = None
        init_messages = ["HW Error"]
        final_messages = ["Minimal Mode"]
    except Exception as e:
        logger.log_error(f"Unexpected error during hardware init: {e}")
        import sys
        sys.print_exception(e)
        button = None
        button_available = False
        volume_pot = None
        init_messages = ["Init Error"]
        final_messages = ["Safe Mode"]

    dm = display_manager.DisplayManager(oled_patterns)

    # ---- ボリューム初期化 ----
    # ここで sound_patterns.is_dfplayer_available() が正しく機能するはず
    try:
        vc = volume_control.PollingVolumeController(volume_pot, sound_patterns, oled_patterns, config)
        initial_volume = vc.init_initial_volume()
        current_volume = None

        if volume_pot and initial_volume is not None and sound_patterns.is_dfplayer_available():
            current_volume = initial_volume
            logger.log_info(f"Initial volume: {current_volume}")
            final_messages += [f"Vol:{current_volume}", "Init End"]
        elif volume_pot and not sound_patterns.is_dfplayer_available():
            logger.log_warning("Volume pot OK, DFPlayer missing.")
            final_messages += ["No Audio", "Init End"]
        elif not volume_pot and sound_patterns.is_dfplayer_available():
            logger.log_warning("DFPlayer OK, no volume pot.")
            final_messages += ["Audio:OK", "No VolCtrl", "Init End"]
        else:
            final_messages += ["No Audio", "Init End"]
    except Exception as e:
        logger.log_error(f"Volume control initialization failed: {e}")
        import sys
        sys.print_exception(e)
        # ダミーのボリュームコントローラを作成
        class DummyVolumeController:
            def poll(self, current_time): pass
            def init_initial_volume(self): return None
        vc = DummyVolumeController()
        current_volume = None
        final_messages += ["No VolCtrl", "Init End"]

    if not button_available:
        final_messages = ["Console Mode"] + final_messages

    try:
        dm.push_message(final_messages)
    except Exception as e:
        logger.log_warning(f"Display message failed: {e}")

    # ---- コンソール表示 ----
    logger.log_info("\n=== Hardware Summary ===")
    logger.log_info(f"Button: {'OK' if button_available else 'N/A'}")
    logger.log_info(f"OLED: {'OK' if oled_patterns.is_oled_available() else 'N/A'}")
    logger.log_info(f"Audio: {'OK' if sound_patterns.is_dfplayer_available() else 'N/A'}")
    logger.log_info(f"NeoPixel: {'OK' if neopixel_controller.is_neopixel_available() else 'N/A'}")
    logger.log_info(f"PWM LED: {'OK' if pwm_led_controller.is_pwm_led_available() else 'N/A'}")
    logger.log_info(f"Volume Pot: {'OK' if volume_pot else 'N/A'}")
    if fallback:
        logger.log_warning("Using fallback scenarios")
    logger.log_info("=========================")

    # ---- LEDで完了表示 ----
    if onboard_led.is_onboard_led_available():
        try:
            blink_times = getattr(config, 'ONBOARD_LED_BLINK_TIMES', 2)
            on_time = getattr(config, 'ONBOARD_LED_ON_TIME_MS', 300)
            off_time = getattr(config, 'ONBOARD_LED_OFF_TIME_MS', 200)
            onboard_led.blink(times=blink_times, on_time_ms=on_time, off_time_ms=off_time)
        except Exception as e:
            logger.log_warning(f"Onboard LED blink failed: {e}")

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
