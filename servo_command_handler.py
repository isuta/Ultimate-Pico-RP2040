# servo_command_handler.py
# サーボモーターコマンドのハンドラー（連続回転型・角度制御型の自動判別）

import config
import servo_rotation_controller
import servo_position_controller
import command_parser

def handle(cmd, stop_flag_ref):
    """
    サーボモーターコマンドを処理します。
    config.pyのSERVO_CONFIGに基づいて自動的に適切なコントローラーに振り分けます。
    
    Args:
        cmd: コマンド辞書
        stop_flag_ref: 停止フラグのリスト参照 [bool]
    """
    command = command_parser.get_param(cmd, "command")
    servo_index = command_parser.get_param(cmd, "servo_index", 0)
    
    if not command:
        print(f"[Warning] Servo command missing 'command' parameter")
        return
    
    # config.pyからサーボ設定を取得
    servo_config = getattr(config, 'SERVO_CONFIG', [])
    if servo_index >= len(servo_config):
        print(f"[Warning] Servo #{servo_index} not configured in SERVO_CONFIG")
        return
    
    servo_type = servo_config[servo_index][1]  # [pin, type]の2番目要素
    
    # タイプに応じて適切なコントローラーに振り分け
    if servo_type == 'continuous':
        _handle_continuous(cmd, command, servo_index, stop_flag_ref)
    elif servo_type == 'position':
        _handle_position(cmd, command, servo_index, stop_flag_ref)
    else:
        print(f"[Warning] Unknown servo type '{servo_type}' for servo #{servo_index}")

def _handle_continuous(cmd, command, servo_index, stop_flag_ref):
    """
    連続回転型サーボのコマンドを処理します。
    
    Args:
        cmd: コマンド辞書
        command: コマンド名 ('rotate', 'stop', 'stop_all')
        servo_index: サーボインデックス
        stop_flag_ref: 停止フラグのリスト参照
    """
    if not servo_rotation_controller.is_servo_available():
        print("[Warning] Continuous servo controller not available")
        return
    
    if command == "rotate":
        speed = command_parser.get_param(cmd, "speed", 0)
        duration_ms = command_parser.get_param(cmd, "duration_ms", 0)
        
        # 速度バリデーション
        speed = command_parser.validate_range(speed, -100, 100, "speed")
        
        if duration_ms > 0:
            # 時間指定回転（ブロッキング、stop_flag対応）
            command_parser.safe_call(
                servo_rotation_controller.rotate_timed,
                servo_index, speed, duration_ms, stop_flag_ref,
                error_context=f"Servo rotation #{servo_index}"
            )
        else:
            # 継続回転（ノンブロッキング）
            command_parser.safe_call(
                servo_rotation_controller.set_speed,
                servo_index, speed,
                error_context=f"Servo set_speed #{servo_index}"
            )
    
    elif command == "stop":
        command_parser.safe_call(
            servo_rotation_controller.stop,
            servo_index,
            error_context=f"Servo stop #{servo_index}"
        )
    
    elif command == "stop_all":
        command_parser.safe_call(
            servo_rotation_controller.stop_all,
            error_context="Servo stop_all"
        )
    
    else:
        print(f"[Warning] Unknown continuous servo command: {command}")

def _handle_position(cmd, command, servo_index, stop_flag_ref):
    """
    角度制御型サーボのコマンドを処理します。
    
    Args:
        cmd: コマンド辞書
        command: コマンド名 ('set_angle', 'center', 'center_all')
        servo_index: サーボインデックス
        stop_flag_ref: 停止フラグのリスト参照
    """
    if not servo_position_controller.is_servo_available():
        print("[Warning] Position servo controller not available")
        return
    
    if command == "set_angle":
        angle = command_parser.get_param(cmd, "angle", 90)
        duration_ms = command_parser.get_param(cmd, "duration_ms", 0)
        
        # 角度バリデーション
        min_angle = getattr(config, 'SERVO_POSITION_MIN_ANGLE', 0)
        max_angle = getattr(config, 'SERVO_POSITION_MAX_ANGLE', 180)
        angle = command_parser.validate_range(angle, min_angle, max_angle, "angle")
        
        if duration_ms > 0:
            # 時間指定保持（ブロッキング、stop_flag対応）
            command_parser.safe_call(
                servo_position_controller.move_angle_timed,
                servo_index, angle, duration_ms, stop_flag_ref,
                error_context=f"Servo set_angle #{servo_index}"
            )
        else:
            # 角度設定のみ（ノンブロッキング）
            command_parser.safe_call(
                servo_position_controller.set_angle,
                servo_index, angle,
                error_context=f"Servo set_angle #{servo_index}"
            )
    
    elif command == "center":
        command_parser.safe_call(
            servo_position_controller.center,
            servo_index,
            error_context=f"Servo center #{servo_index}"
        )
    
    elif command == "center_all":
        command_parser.safe_call(
            servo_position_controller.center_all,
            error_context="Servo center_all"
        )
    
    else:
        print(f"[Warning] Unknown position servo command: {command}")
