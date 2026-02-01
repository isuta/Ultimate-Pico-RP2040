# servo_position_controller.py
# 角度制御型サーボモーター（SG90等）の制御モジュール
# 0～180度の位置制御
# config.pyのSERVO_TYPESで'position'と指定されたサーボのみ対象

import config
from machine import Pin, PWM
import time
import servo_pwm_utils

# PWMインスタンスを格納するリスト（servo_rotation_controllerと同じインデックス）
servos = []
# 利用可能なサーボのインデックス（角度制御型のみ）
available_servos = set()

def is_servo_available():
    """
    いずれかの角度制御型サーボが利用可能かどうかを返します。
    """
    return len(available_servos) > 0

def get_available_servos():
    """
    利用可能な角度制御型サーボインデックスのセットを返します。
    """
    return available_servos.copy()

def angle_to_pulse_width(angle):
    """
    角度（0～180度）をパルス幅（μs）に変換
    
    Args:
        angle: 角度（0～180度）
    
    Returns:
        パルス幅（μs）
    """
    min_angle = getattr(config, 'SERVO_POSITION_MIN_ANGLE', 0)
    max_angle = getattr(config, 'SERVO_POSITION_MAX_ANGLE', 180)
    min_pulse = getattr(config, 'SERVO_POSITION_MIN_PULSE', 1000)
    max_pulse = getattr(config, 'SERVO_POSITION_MAX_PULSE', 2000)
    
    # 角度範囲チェック
    angle = max(min_angle, min(max_angle, angle))
    
    # 線形補間でパルス幅を計算
    angle_range = max_angle - min_angle
    pulse_range = max_pulse - min_pulse
    pulse_width_us = min_pulse + ((angle - min_angle) / angle_range) * pulse_range
    
    return int(pulse_width_us)

def init_servos():
    """
    config.pyで定義されたサーボモーターのうち、角度制御型を初期化します。
    各サーボは個別にエラーハンドリングされ、失敗したサーボはスキップされます。
    """
    global servos, available_servos
    
    servo_config = getattr(config, 'SERVO_CONFIG', [])
    frequency = getattr(config, 'SERVO_FREQUENCY', 50)
    
    if not servo_config:
        print("Servo Position: No pins configured")
        return
    
    servos = [None] * len(servo_config)
    available_servos = set()
    
    for i, servo_def in enumerate(servo_config):
        pin_num = servo_def[0]
        servo_type = servo_def[1]
        
        # 角度制御型のみ初期化
        if servo_type != 'position':
            continue
        
        try:
            pin = Pin(pin_num)
            pwm = PWM(pin)
            pwm.freq(frequency)
            
            # 初期状態: 中央位置（90度、1500μs）
            center_duty = servo_pwm_utils.pulse_width_to_duty(1500, frequency)
            pwm.duty_u16(center_duty)
            
            servos[i] = pwm
            available_servos.add(i)
            
            print(f"Servo Position #{i} (GP{pin_num}): 初期化成功（中央90度）")
            
        except OSError as e:
            print(f"Servo Position #{i} (GP{pin_num}): GPIO初期化失敗 - {e}")
            servos[i] = None
        except Exception as e:
            print(f"Servo Position #{i} (GP{pin_num}): 初期化エラー - {e}")
            import sys
            sys.print_exception(e)
            servos[i] = None
    
    if available_servos:
        print(f"Servo Position: 初期化成功 - 利用可能サーボ: {list(available_servos)}")
    else:
        print("Servo Position: 角度制御型サーボなし")

def set_angle(servo_index, angle):
    """
    指定されたサーボの角度を設定します。
    
    Args:
        servo_index: サーボインデックス (0-2)
        angle: 角度（0～180度）
    
    Returns:
        成功した場合True、失敗した場合False
    """
    if servo_index < 0 or servo_index >= len(servos):
        print(f"[Error] Invalid servo index: {servo_index}")
        return False
    
    if servo_index not in available_servos:
        print(f"[Warning] Servo Position #{servo_index} is not available")
        return False
    
    # 角度範囲チェック
    min_angle = getattr(config, 'SERVO_POSITION_MIN_ANGLE', 0)
    max_angle = getattr(config, 'SERVO_POSITION_MAX_ANGLE', 180)
    
    if not min_angle <= angle <= max_angle:
        print(f"[Warning] Angle {angle} out of range ({min_angle}～{max_angle}), clamping.")
        angle = max(min_angle, min(max_angle, angle))
    
    try:
        frequency = getattr(config, 'SERVO_FREQUENCY', 50)

        # 個体差対応のキャリブレーション設定（任意）
        calib = getattr(config, 'SERVO_POSITION_CALIB', {})
        per_servo = calib.get(servo_index, {})

        min_angle = getattr(config, 'SERVO_POSITION_MIN_ANGLE', 0)
        max_angle = getattr(config, 'SERVO_POSITION_MAX_ANGLE', 180)
        # サーボ個体に合わせてパルス幅を上書き可能
        min_pulse = per_servo.get('min_pulse', getattr(config, 'SERVO_POSITION_MIN_PULSE', 1000))
        max_pulse = per_servo.get('max_pulse', getattr(config, 'SERVO_POSITION_MAX_PULSE', 2000))
        offset_deg = per_servo.get('offset_deg', 0)

        # オフセット適用後の角度を算出し、範囲内にクリップ
        effective_angle = angle + offset_deg
        if effective_angle < min_angle:
            effective_angle = min_angle
        elif effective_angle > max_angle:
            effective_angle = max_angle

        # 線形補間でパルス幅を計算（個体用min/maxを反映）
        angle_range = max_angle - min_angle
        pulse_range = max_pulse - min_pulse
        pulse_width_us = min_pulse + ((effective_angle - min_angle) / angle_range) * pulse_range

        duty = servo_pwm_utils.pulse_width_to_duty(pulse_width_us, frequency)
        servos[servo_index].duty_u16(duty)

        return True
        
    except OSError as e:
        print(f"[Hardware Error] Servo Position #{servo_index} angle set failed: {e}")
        return False
    except Exception as e:
        print(f"[Error] Servo Position #{servo_index} error: {e}")
        import sys
        sys.print_exception(e)
        return False

def move_angle_timed(servo_index, angle, duration_ms, stop_flag_ref=None):
    """
    指定されたサーボを指定角度に移動させ、指定時間保持します（ブロッキング）。
    stop_flag_refによる協調的キャンセルに対応。
    
    Args:
        servo_index: サーボインデックス (0-2)
        angle: 目標角度（0～180度）
        duration_ms: 保持時間 (ミリ秒)、0以下の場合は保持し続ける
        stop_flag_ref: 停止フラグのリスト参照 [bool] (オプション)
    
    Returns:
        正常完了した場合True、中断/エラーの場合False
    """
    if servo_index < 0 or servo_index >= len(servos):
        print(f"[Error] Invalid servo index: {servo_index}")
        return False
    
    if servo_index not in available_servos:
        print(f"[Warning] Servo Position #{servo_index} is not available")
        return False
    
    # 角度設定
    if not set_angle(servo_index, angle):
        return False
    
    # duration_msが0以下の場合は保持し続ける
    if duration_ms <= 0:
        return True
    
    # 指定時間待機（停止フラグ監視）
    check_interval_ms = getattr(config, 'SERVO_ROTATION_CHECK_INTERVAL_MS', 50)
    start_time = time.ticks_ms()
    
    try:
        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
            # 停止フラグチェック
            if stop_flag_ref and stop_flag_ref[0]:
                print(f"[Info] Servo Position #{servo_index} movement interrupted by stop_flag")
                # 角度制御型は現在位置を保持（中央に戻さない）
                return False
            
            time.sleep_ms(check_interval_ms)
        
        return True
        
    except Exception as e:
        print(f"[Error] Servo Position #{servo_index} timed movement error: {e}")
        import sys
        sys.print_exception(e)
        return False

def center(servo_index):
    """
    指定されたサーボを中央位置（90度）に戻します。
    
    Args:
        servo_index: サーボインデックス (0-2)
    """
    return set_angle(servo_index, 90)

def center_all():
    """
    全てのサーボを中央位置（90度）に戻します。
    """
    for index in available_servos:
        center(index)
    print("Servo Position: 全サーボを中央位置に戻しました")

def cleanup():
    """
    全サーボを中央位置に戻してPWMを解放します（終了処理）。
    """
    print("Servo Position: クリーンアップを開始")
    center_all()
    
    for i, pwm in enumerate(servos):
        if pwm is not None:
            try:
                pwm.deinit()
            except Exception as e:
                print(f"Servo Position #{i}: deinit failed - {e}")
    
    print("Servo Position: クリーンアップ完了")
