# led_command_handler.py
# NeoPixel LEDコマンドのハンドラー

import neopixel_controller
import command_parser

def handle(cmd, stop_flag_ref):
    """
    NeoPixel LEDコマンドを処理します。
    
    Args:
        cmd: コマンド辞書
        stop_flag_ref: 停止フラグのリスト参照 [bool]
    """
    command = command_parser.get_param(cmd, "command")
    
    if not command:
        print(f"[Warning] LED command missing 'command' parameter")
        return
    
    if command == 'off':
        _handle_off(stop_flag_ref)
    elif command == 'fill':
        _handle_fill(cmd, stop_flag_ref)
    else:
        print(f"[Warning] Unknown led command: {command}")

def _handle_off(stop_flag_ref):
    """
    全NeoPixel LEDを消灯します。
    
    Args:
        stop_flag_ref: 停止フラグのリスト参照
    """
    command_parser.safe_call(
        neopixel_controller.pattern_off,
        stop_flag_ref,
        error_context="LED off"
    )

def _handle_fill(cmd, stop_flag_ref):
    """
    指定したストリップを単色で塗りつぶします。
    
    Args:
        cmd: コマンド辞書
        stop_flag_ref: 停止フラグのリスト参照
    """
    strip_name = command_parser.get_param(cmd, "strip", "all")
    color = command_parser.get_param(cmd, "color")
    duration_ms = command_parser.get_param(cmd, "duration", 0)
    
    # カラーバリデーション
    validated_color = command_parser.validate_color(color)
    if not validated_color:
        return
    
    r, g, b = validated_color
    
    # NeoPixel利用可能チェック
    if not neopixel_controller.is_neopixel_available():
        print(f"[Warning] LED: fill {strip_name} を ({r}, {g}, {b})（スキップ - NeoPixel利用不可）")
        return
    
    # LED設定
    command_parser.safe_call(
        neopixel_controller.set_global_leds_by_indices,
        strip_name, r, g, b,
        error_context=f"LED fill {strip_name}"
    )
    
    # duration指定がある場合は待機
    if duration_ms > 0:
        interrupted = not command_parser.wait_with_stop_check(duration_ms, stop_flag_ref)
        if interrupted:
            print("LED点灯を中断します。")
            stop_flag_ref[0] = False
