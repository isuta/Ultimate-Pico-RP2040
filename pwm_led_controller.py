# pwm_led_controller.py
import config
from machine import Pin, PWM
import time
import math

# PWM LEDインスタンスを格納するリスト
pwm_leds = []
# 各LEDの現在の輝度を保持 (0-100%)
led_brightness_cache = []
# 利用可能なLEDのインデックス
available_leds = set()

def is_pwm_led_available():
    """
    いずれかのPWM LEDが利用可能かどうかを返します。
    """
    return len(available_leds) > 0

def get_available_leds():
    """
    利用可能なLEDインデックスのセットを返します。
    """
    return available_leds.copy()

def brightness_to_duty(brightness):
    """
    輝度（0-100%）をPWMデューティ比（0-65535）に変換
    ガンマ補正を適用して、人間の目に自然な明るさに変換
    
    Args:
        brightness: 輝度パーセント (0-100)
    
    Returns:
        PWMデューティ比 (0-65535)
    """
    gamma = getattr(config, 'PWM_LED_GAMMA', 2.2)
    max_duty = getattr(config, 'PWM_LED_MAX_DUTY', 65535)
    
    # 0-100% を 0.0-1.0 に正規化
    normalized = max(0.0, min(100.0, brightness)) / 100.0
    
    # ガンマ補正を適用
    corrected = math.pow(normalized, gamma)
    
    # PWMデューティ比に変換
    duty = int(corrected * max_duty)
    
    return duty

def init_pwm_leds():
    """
    config.pyで定義されたPWM LEDを初期化します。
    各LEDは個別にエラーハンドリングされ、失敗したLEDはスキップされます。
    """
    global pwm_leds, led_brightness_cache, available_leds
    
    pwm_leds = []
    led_brightness_cache = []
    available_leds = set()
    
    led_pins = getattr(config, 'PWM_LED_PINS', [])
    frequency = getattr(config, 'PWM_LED_FREQUENCY', 1000)
    
    if not led_pins:
        print("PWM LED: No pins configured")
        return
    
    for index, pin_num in enumerate(led_pins):
        try:
            pin = Pin(pin_num)
            pwm = PWM(pin)
            pwm.freq(frequency)
            pwm.duty_u16(0)  # 初期状態は消灯
            
            pwm_leds.append(pwm)
            led_brightness_cache.append(0)  # 初期輝度は0%
            available_leds.add(index)
            
            print(f"PWM LED #{index} (GP{pin_num}): 初期化成功")
            
        except OSError as e:
            print(f"PWM LED #{index} (GP{pin_num}): GPIO初期化失敗 - {e}")
            pwm_leds.append(None)
            led_brightness_cache.append(0)
        except Exception as e:
            print(f"PWM LED #{index} (GP{pin_num}): 初期化エラー - {e}")
            import sys
            sys.print_exception(e)
            pwm_leds.append(None)
            led_brightness_cache.append(0)
    
    if available_leds:
        print(f"PWM LED: 初期化成功 - 利用可能LED: {list(available_leds)}")
    else:
        print("PWM LED: 全LED初期化失敗 - PWM LED機能は無効")

def set_brightness(led_index, brightness, update_cache=True):
    """
    指定されたLEDの輝度を即座に設定します。
    
    Args:
        led_index: LEDインデックス (0-3)
        brightness: 輝度パーセント (0-100)
        update_cache: キャッシュを更新するか (デフォルト: True)
    
    Returns:
        成功した場合True、失敗した場合False
    """
    if led_index < 0 or led_index >= len(pwm_leds):
        print(f"[Error] Invalid LED index: {led_index}")
        return False
    
    if pwm_leds[led_index] is None:
        print(f"[Warning] LED #{led_index} is not available")
        return False
    
    try:
        duty = brightness_to_duty(brightness)
        pwm_leds[led_index].duty_u16(duty)
        
        if update_cache:
            led_brightness_cache[led_index] = brightness
        
        return True
        
    except OSError as e:
        print(f"[Hardware Error] LED #{led_index} set brightness failed: {e}")
        return False
    except Exception as e:
        print(f"[Error] LED #{led_index} brightness control error: {e}")
        import sys
        sys.print_exception(e)
        return False

def fade_pwm_led(led_index, target_brightness, duration_ms, stop_flag_ref=None):
    """
    指定されたLEDを現在の輝度から目標輝度までフェードします（ブロッキング）。
    stop_flag_refによる協調的キャンセルに対応。
    
    Args:
        led_index: LEDインデックス (0-3)
        target_brightness: 目標輝度パーセント (0-100)
        duration_ms: フェード時間 (ミリ秒)
        stop_flag_ref: 停止フラグのリスト参照 [bool] (オプション)
    
    Returns:
        正常完了した場合True、中断/エラーの場合False
    """
    if led_index < 0 or led_index >= len(pwm_leds):
        print(f"[Error] Invalid LED index: {led_index}")
        return False
    
    if pwm_leds[led_index] is None:
        print(f"[Warning] LED #{led_index} is not available")
        return False
    
    # 現在の輝度を取得
    start_brightness = led_brightness_cache[led_index]
    
    # フェード不要な場合
    if start_brightness == target_brightness:
        return True
    
    if duration_ms <= 0:
        # 時間が0以下の場合は即座に設定
        return set_brightness(led_index, target_brightness)
    
    # フェードパラメータの計算
    step_interval_ms = getattr(config, 'PWM_FADE_STEP_INTERVAL_MS', 10)
    total_steps = max(1, duration_ms // step_interval_ms)
    brightness_diff = target_brightness - start_brightness
    brightness_step = brightness_diff / total_steps
    
    start_time = time.ticks_ms()
    
    try:
        for step in range(total_steps + 1):
            # 停止フラグチェック
            if stop_flag_ref and stop_flag_ref[0]:
                print(f"[Info] LED #{led_index} fade interrupted by stop_flag")
                return False
            
            # 経過時間から現在の輝度を計算
            elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
            if elapsed_ms >= duration_ms:
                # 最終ステップ：正確に目標値に設定
                set_brightness(led_index, target_brightness)
                break
            
            # 進捗率から現在の輝度を計算
            progress = elapsed_ms / duration_ms
            current_brightness = start_brightness + (brightness_diff * progress)
            
            # 輝度を設定
            set_brightness(led_index, current_brightness)
            
            # 次のステップまで待機
            time.sleep_ms(step_interval_ms)
        
        return True
        
    except Exception as e:
        print(f"[Error] LED #{led_index} fade error: {e}")
        import sys
        sys.print_exception(e)
        return False

def turn_on(led_index, brightness=100):
    """
    指定されたLEDを点灯します（set_brightnessのラッパー）。
    
    Args:
        led_index: LEDインデックス (0-3)
        brightness: 輝度パーセント (0-100、デフォルト: 100)
    """
    return set_brightness(led_index, brightness)

def turn_off(led_index):
    """
    指定されたLEDを消灯します。
    
    Args:
        led_index: LEDインデックス (0-3)
    """
    return set_brightness(led_index, 0)

def all_off():
    """
    全てのPWM LEDを消灯します。
    """
    for index in available_leds:
        turn_off(index)

def get_brightness(led_index):
    """
    指定されたLEDの現在の輝度を取得します。
    
    Args:
        led_index: LEDインデックス (0-3)
    
    Returns:
        輝度パーセント (0-100)、エラーの場合None
    """
    if led_index < 0 or led_index >= len(led_brightness_cache):
        return None
    return led_brightness_cache[led_index]
