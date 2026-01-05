# servo_pwm_utils.py
# サーボモーター制御の共通ユーティリティ
# servo_rotation_controller と servo_position_controller で共有

import config

def pulse_width_to_duty(pulse_width_us, frequency=None):
    """
    パルス幅（μs）をデューティサイクル（16bit）に変換
    
    Args:
        pulse_width_us: パルス幅（μs）
        frequency: PWM周波数（Hz）、Noneの場合はconfigから取得
    
    Returns:
        デューティサイクル（0～65535）
    """
    if frequency is None:
        frequency = getattr(config, 'SERVO_FREQUENCY', 50)
    
    period_us = 1_000_000 / frequency  # 50Hz → 20000μs
    duty_ratio = pulse_width_us / period_us
    duty_u16 = round(duty_ratio * 65535)
    return duty_u16
