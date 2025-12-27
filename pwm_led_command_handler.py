# pwm_led_command_handler.py
# PWM LED（単色LED）コマンドのハンドラー

import pwm_led_controller
import command_parser

def handle(cmd, stop_flag_ref):
    """
    PWM LEDコマンドを処理します（旧形式対応）。
    
    Args:
        cmd: コマンド辞書
        stop_flag_ref: 停止フラグのリスト参照 [bool]
    """
    # 旧形式のコマンドキーをチェック
    if 'led_on' in cmd:
        _handle_led_on(cmd['led_on'])
    elif 'led_off' in cmd:
        _handle_led_off(cmd['led_off'])
    elif 'led_fade_in' in cmd:
        _handle_led_fade_in(cmd['led_fade_in'], stop_flag_ref)
    elif 'led_fade_out' in cmd:
        _handle_led_fade_out(cmd['led_fade_out'], stop_flag_ref)
    else:
        print(f"[Warning] Unknown PWM LED command format: {cmd}")

def _handle_led_on(params):
    """
    PWM LEDを点灯します。
    
    Args:
        params: パラメータ辞書
    """
    led_index = command_parser.get_param(params, 'led_index', 0)
    brightness = command_parser.get_param(params, 'max_brightness', 100)
    
    # 輝度バリデーション
    brightness = command_parser.validate_range(brightness, 0, 100, "brightness")
    
    if not pwm_led_controller.is_pwm_led_available():
        print(f"[Warning] PWM LED: LED #{led_index} 点灯（スキップ - PWM LED利用不可）")
        return
    
    command_parser.safe_call(
        pwm_led_controller.set_brightness,
        led_index, brightness,
        error_context=f"PWM LED on #{led_index}"
    )

def _handle_led_off(params):
    """
    PWM LEDを消灯します。
    
    Args:
        params: パラメータ辞書
    """
    led_index = command_parser.get_param(params, 'led_index', 0)
    
    if not pwm_led_controller.is_pwm_led_available():
        print(f"[Warning] PWM LED: LED #{led_index} 消灯（スキップ - PWM LED利用不可）")
        return
    
    command_parser.safe_call(
        pwm_led_controller.set_brightness,
        led_index, 0,
        error_context=f"PWM LED off #{led_index}"
    )

def _handle_led_fade_in(params, stop_flag_ref):
    """
    PWM LEDをフェードインします。
    
    Args:
        params: パラメータ辞書
        stop_flag_ref: 停止フラグのリスト参照
    """
    led_index = command_parser.get_param(params, 'led_index', 0)
    duration_ms = command_parser.get_param(params, 'duration_ms', 0)
    brightness = command_parser.get_param(params, 'max_brightness', 100)
    
    # 輝度バリデーション
    brightness = command_parser.validate_range(brightness, 0, 100, "brightness")
    
    if not pwm_led_controller.is_pwm_led_available():
        print(f"[Warning] PWM LED: LED #{led_index} フェードイン（スキップ - PWM LED利用不可）")
        return
    
    command_parser.safe_call(
        pwm_led_controller.fade_pwm_led,
        led_index, brightness, duration_ms, stop_flag_ref,
        error_context=f"PWM LED fade_in #{led_index}"
    )

def _handle_led_fade_out(params, stop_flag_ref):
    """
    PWM LEDをフェードアウトします。
    
    Args:
        params: パラメータ辞書
        stop_flag_ref: 停止フラグのリスト参照
    """
    led_index = command_parser.get_param(params, 'led_index', 0)
    duration_ms = command_parser.get_param(params, 'duration_ms', 0)
    
    if not pwm_led_controller.is_pwm_led_available():
        print(f"[Warning] PWM LED: LED #{led_index} フェードアウト（スキップ - PWM LED利用不可）")
        return
    
    command_parser.safe_call(
        pwm_led_controller.fade_pwm_led,
        led_index, 0, duration_ms, stop_flag_ref,
        error_context=f"PWM LED fade_out #{led_index}"
    )
