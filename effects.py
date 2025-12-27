# effects.py
# コマンドディスパッチャー - JSONコマンドを各ハンドラーに振り分ける

import config
import time

import sound_patterns
from stepper_motor import StepperMotor

# コマンドハンドラーをインポート
import command_parser
import servo_command_handler
import led_command_handler
import pwm_led_command_handler
import motor_command_handler
import sound_command_handler

# motor変数をモジュールレベルで初期化
motor = None 

def init():
    """モジュール初期化：モーターなどの外部デバイスを安全に初期化"""
    global motor
    try:
        motor = StepperMotor(debug=True)
        print("[Init] StepperMotor 初期化完了")
    except OSError as e:
        print(f"[Hardware Error] StepperMotor GPIO initialization failed: {e}")
        motor = None
    except ValueError as e:
        print(f"[Config Error] Invalid StepperMotor configuration: {e}")
        motor = None
    except Exception as e:
        print(f"[Error] StepperMotor 初期化失敗: {e}")
        import sys
        sys.print_exception(e)
        motor = None

def execute_command(command_list, stop_flag_ref):
    """
    JSONで定義されたコマンドリスト（リスト形式または辞書形式）を順番に実行します。
    実行終了後、モーターの通電を解除して停止させます。
    """
    motor_used = False  # モーターコマンドが実行されたかを追跡
    
    try:
        for cmd in command_list:
            # 停止フラグチェック
            if command_parser.check_stop_flag(stop_flag_ref):
                print("[Info] 停止フラグが検出されました。コマンドを中断します。")
                sound_patterns.stop_playback()
                stop_flag_ref[0] = False
                return

            # コマンドタイプ判定
            cmd_type = command_parser.parse_command_type(cmd)
            
            if not cmd_type:
                print(f"[Warning] Unknown command format or empty command: {cmd}")
                continue

            try:
                # コマンドタイプごとにハンドラーへディスパッチ
                if cmd_type == 'servo':
                    servo_command_handler.handle(cmd, stop_flag_ref)
                
                elif cmd_type == 'led':
                    led_command_handler.handle(cmd, stop_flag_ref)
                
                elif cmd_type == 'motor':
                    motor_used = True  # モーターコマンドが実行された
                    motor_command_handler.handle(cmd, motor, stop_flag_ref)
                
                elif cmd_type == 'sound':
                    sound_command_handler.handle(cmd, stop_flag_ref)
                
                elif cmd_type == 'delay':
                    _handle_delay(cmd, stop_flag_ref)
                
                elif cmd_type == 'wait_ms':
                    _handle_wait_ms(cmd, stop_flag_ref)
                
                elif cmd_type == 'stop_playback':
                    _handle_stop_playback()
                
                # PWM LED旧形式（led_on, led_off, led_fade_in, led_fade_out）
                elif cmd_type in ['led_on', 'led_off', 'led_fade_in', 'led_fade_out']:
                    pwm_led_command_handler.handle(cmd, stop_flag_ref)
                
                elif cmd_type == 'effect':
                    # effectコマンドは予約（将来の拡張用）
                    print(f"[Warning] 'effect' command not yet implemented")
                
                else:
                    print(f"[Warning] Unknown command type: {cmd_type}")

            except Exception as e:
                print(f"[Error] Command execution failed: {cmd_type}")
                import sys
                sys.print_exception(e)
                # エラーでも続行

    finally:
        # 終了処理: モーター通電解除（モーターコマンドが実行された場合のみ）
        if motor_used and motor:
            try:
                motor.release()
                print("[Effects] StepperMotor通電解除完了")
            except Exception as e:
                print(f"[Warning] Motor release failed: {e}")

def _handle_delay(cmd, stop_flag_ref):
    """delay コマンドを処理（辞書形式・リスト形式両対応）"""
    if isinstance(cmd, dict):
        duration_ms = command_parser.get_param(cmd, "duration", 0)
    elif isinstance(cmd, list) and len(cmd) == 2:
        duration_ms = cmd[1]
    else:
        print(f"[Warning] Invalid delay command format: {cmd}")
        return
    
    if not command_parser.validate_positive(duration_ms, "delay duration"):
        return
    
    command_parser.wait_with_stop_check(duration_ms, stop_flag_ref)

def _handle_wait_ms(cmd, stop_flag_ref):
    """wait_ms コマンドを処理（旧形式）"""
    duration_ms = command_parser.get_param(cmd, 'wait_ms', 0)
    
    if not command_parser.validate_positive(duration_ms, "wait_ms"):
        return
    
    interrupted = not command_parser.wait_with_stop_check(duration_ms, stop_flag_ref)
    if interrupted:
        print("[Info] Wait中断します。")
        stop_flag_ref[0] = False

def _handle_stop_playback():
    """全モジュールの停止処理"""
    print("[Info] 全モジュール停止コマンドを実行します。")
    
    command_parser.safe_call(
        sound_patterns.stop_playback,
        error_context="Sound stop"
    )
    
    # 他のモジュール停止処理はここに追加可能
