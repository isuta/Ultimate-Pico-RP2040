# servo_rotation_controller.py
# 連続回転サーボモーター（SG90-HV等）の制御モジュール
# GP5, GP6, GP7の3つのサーボを独立制御

import config
from machine import Pin, PWM
import time
import servo_pwm_utils

# PWMインスタンスを格納するリスト
servos = []
# 利用可能なサーボのインデックス
available_servos = set()

def is_servo_available():
    """
    いずれかのサーボが利用可能かどうかを返します。
    """
    return len(available_servos) > 0

def get_available_servos():
    """
    利用可能なサーボインデックスのセットを返します。
    """
    return available_servos.copy()

def speed_to_pulse_width(speed):
    """
    速度パラメータ（-100～100）をパルス幅（μs）に変換
    
    Args:
        speed: -100（最速逆転）～ 0（停止）～ 100（最速正転）
    
    Returns:
        パルス幅（μs）: 1000～2000
    """
    # speedを-100～100から0～100に正規化
    normalized = (speed + 100) / 2  # 0～100
    # パルス幅に変換（1000μs～2000μs）
    pulse_width_us = 1000 + (normalized * 10)
    return int(pulse_width_us)

def init_servos():
    """
    config.pyで定義されたサーボモーターを初期化します。
    各サーボは個別にエラーハンドリングされ、失敗したサーボはスキップされます。
    """
    global servos, available_servos
    
    servo_config = getattr(config, 'SERVO_CONFIG', [])
    frequency = getattr(config, 'SERVO_FREQUENCY', 50)
    
    if not servo_config:
        print("Servo: No pins configured")
        return
    
    servos = [None] * len(servo_config)
    available_servos = set()
    
    for i, servo_def in enumerate(servo_config):
        pin_num = servo_def[0]
        servo_type = servo_def[1]
        
        # 連続回転型のみ初期化
        if servo_type != 'continuous':
            continue
        try:
            pin = Pin(pin_num)
            pwm = PWM(pin)
            pwm.freq(frequency)
            
            # 初期状態: PWM信号をオフ（完全停止）
            # 連続回転サーボは個体差で1500μsでも微妙に動くことがあるため
            # 使用しない時はPWM信号を完全にオフにする
            pwm.duty_u16(0)
            
            servos[i] = pwm
            available_servos.add(i)
            
            print(f"Servo #{i} (GP{pin_num}): 初期化成功（PWMオフ）")
            
        except OSError as e:
            print(f"Servo #{i} (GP{pin_num}): GPIO初期化失敗 - {e}")
            servos[i] = None
        except Exception as e:
            print(f"Servo #{i} (GP{pin_num}): 初期化エラー - {e}")
            import sys
            sys.print_exception(e)
            servos[i] = None
    
    if available_servos:
        print(f"Servo: 初期化成功 - 利用可能サーボ: {list(available_servos)}")
    else:
        print("Servo: 全サーボ初期化失敗 - サーボ機能は無効")

def set_speed(servo_index, speed):
    """
    指定されたサーボの速度を設定します。
    
    Args:
        servo_index: サーボインデックス (0-2)
        speed: 速度（-100～100）
               -100: 最速逆転（1000μs）
               0: 停止（1500μs）
               100: 最速正転（2000μs）
    
    Returns:
        成功した場合True、失敗した場合False
    """
    if servo_index < 0 or servo_index >= len(servos):
        print(f"[Error] Invalid servo index: {servo_index}")
        return False
    
    if servo_index not in available_servos:
        print(f"[Warning] Servo #{servo_index} is not available")
        return False
    
    # 速度範囲チェック
    if not -100 <= speed <= 100:
        print(f"[Warning] Speed {speed} out of range (-100～100), clamping.")
        speed = max(-100, min(100, speed))

    try:
        pulse_width_us = speed_to_pulse_width(speed)
        duty = servo_pwm_utils.pulse_width_to_duty(pulse_width_us)
        servos[servo_index].duty_u16(duty)

        return True

    except OSError as e:
        print(f"[Hardware Error] Servo #{servo_index} speed set failed: {e}")
        return False
    except Exception as e:
        print(f"[Error] Servo #{servo_index} error: {e}")
        import sys
        sys.print_exception(e)
        return False

def rotate_timed(servo_index, speed, duration_ms, stop_flag_ref=None):
    """
    指定されたサーボを指定時間だけ回転させます（ブロッキング）。
    stop_flag_refによる協調的キャンセルに対応。
    
    Args:
        servo_index: サーボインデックス (0-2)
        speed: 速度（-100～100）
        duration_ms: 回転時間 (ミリ秒)
        stop_flag_ref: 停止フラグのリスト参照 [bool] (オプション)
    
    Returns:
        正常完了した場合True、中断/エラーの場合False
    """
    if servo_index < 0 or servo_index >= len(servos):
        print(f"[Error] Invalid servo index: {servo_index}")
        return False
    
    if servo_index not in available_servos:
        print(f"[Warning] Servo #{servo_index} is not available")
        return False
    
    # 速度設定
    if not set_speed(servo_index, speed):
        return False
    
    # duration_msが0以下の場合は継続回転（停止しない）
    if duration_ms <= 0:
        return True
    
    # 指定時間待機（停止フラグ監視）
    check_interval_ms = getattr(config, 'SERVO_ROTATION_CHECK_INTERVAL_MS', 50)
    start_time = time.ticks_ms()
    
    try:
        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
            # 停止フラグチェック
            if stop_flag_ref and stop_flag_ref[0]:
                print(f"[Info] Servo #{servo_index} rotation interrupted by stop_flag")
                stop(servo_index)
                return False
            
            time.sleep_ms(check_interval_ms)
        
        # 自動停止
        stop(servo_index)
        return True
        
    except Exception as e:
        print(f"[Error] Servo #{servo_index} timed rotation error: {e}")
        import sys
        sys.print_exception(e)
        stop(servo_index)
        return False

def stop(servo_index):
    """
    指定されたサーボを停止します（PWM信号をオフ）。
    連続回転サーボは個体差で1500μsでも微妙に動くため、
    完全停止にはPWM信号をオフにします。
    
    Args:
        servo_index: サーボインデックス (0-2)
    """
    if servo_index < 0 or servo_index >= len(servos):
        print(f"[Error] Invalid servo index: {servo_index}")
        return False
    
    if servo_index not in available_servos:
        print(f"[Warning] Servo #{servo_index} is not available")
        return False
    
    try:
        servos[servo_index].duty_u16(0)  # PWM信号をオフ
        return True
    except Exception as e:
        print(f"[Error] Failed to stop servo #{servo_index}: {e}")
        return False

def stop_all():
    """
    全てのサーボを停止します（PWM信号をオフ）。
    """
    for index in available_servos:
        stop(index)
    print("Servo: 全サーボを停止しました（PWMオフ）")

def cleanup():
    """
    全サーボを停止してPWMを解放します（終了処理）。
    """
    print("Servo: クリーンアップを開始")
    stop_all()
    
    for i, pwm in enumerate(servos):
        if pwm is not None:
            try:
                pwm.deinit()
            except Exception as e:
                print(f"Servo #{i}: deinit failed - {e}")
    
    print("Servo: クリーンアップ完了")
