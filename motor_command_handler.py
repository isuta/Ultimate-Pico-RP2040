# motor_command_handler.py
# ステッピングモーターコマンドのハンドラー

import command_parser

def handle(cmd, motor, stop_flag_ref):
    """
    ステッピングモーターコマンドを処理します。
    
    Args:
        cmd: コマンド辞書
        motor: StepperMotorインスタンス（effects.pyから渡される）
        stop_flag_ref: 停止フラグのリスト参照 [bool]
    """
    if not motor:
        print("[Warning] モーター制御スキップ（モジュール未初期化）")
        return
    
    command = command_parser.get_param(cmd, "command")
    
    if not command:
        print(f"[Warning] Motor command missing 'command' parameter")
        return
    
    if command == "rotate":
        _handle_rotate(cmd, motor)
    elif command == "step":
        _handle_step(cmd, motor)
    else:
        print(f"[Warning] Unknown motor command: {command}")

def _handle_rotate(cmd, motor):
    """
    ステッピングモーターを角度指定で回転します。
    
    Args:
        cmd: コマンド辞書
        motor: StepperMotorインスタンス
    """
    angle = command_parser.get_param(cmd, "angle", 0)
    speed = command_parser.get_param(cmd, "speed", 200)
    direction = command_parser.get_param(cmd, "direction", 1)
    
    # 方向バリデーション
    if direction not in [1, -1]:
        print(f"[Warning] Invalid direction {direction}, using 1")
        direction = 1
    
    command_parser.safe_call(
        motor.rotate_degrees,
        angle, speed, direction,
        error_context=f"Motor rotate {angle}°"
    )

def _handle_step(cmd, motor):
    """
    ステッピングモーターをステップ数指定で回転します。
    
    Args:
        cmd: コマンド辞書
        motor: StepperMotorインスタンス
    """
    steps = command_parser.get_param(cmd, "steps", 0)
    direction = command_parser.get_param(cmd, "direction", 1)
    
    # 方向バリデーション
    if direction not in [1, -1]:
        print(f"[Warning] Invalid direction {direction}, using 1")
        direction = 1
    
    command_parser.safe_call(
        motor.move_steps,
        steps, direction,
        error_context=f"Motor step {steps}"
    )
