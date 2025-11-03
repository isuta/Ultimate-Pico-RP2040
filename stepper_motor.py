# ステッピングモーター制御コード (角度指定制御版 - 実測値補正済み)
# Raspberry Pi Pico W / MicroPython / DRV8835使用
# 🚨 変更点: 回転状態をグローバル変数で管理し、非ブロッキング動作を実現します。

from machine import Pin
import utime
import config 
import sys # デバッグ用にutimeの存在を確認

# 🚨 新しいグローバル状態変数
_motor_is_rotating = False
_target_steps = 0
_steps_remaining = 0
_step_delay_ms = 0
_last_step_time = 0
_direction = 1
_step_sequence_map = None
_current_map_index = 0

# --- 制御ピンの定義 (config.pyからピン番号を取得して初期化) ---
AIN1 = Pin(config.PIN_AIN1, Pin.OUT) 
AIN2 = Pin(config.PIN_AIN2, Pin.OUT) 
BIN1 = Pin(config.PIN_BIN1, Pin.OUT) 
BIN2 = Pin(config.PIN_BIN2, Pin.OUT) 

if config.PIN_nSLEEP is not None:
    nSLEEP = Pin(config.PIN_nSLEEP, Pin.OUT) 
else:
    nSLEEP = None

PINS = [AIN1, AIN2, BIN1, BIN2]

# --- 励磁シーケンス (ハーフステップ駆動 - 標準8ステップ) ---
HALF_STEP_SEQUENCE = [
    [1, 0, 0, 0], [1, 0, 1, 0], [0, 0, 1, 0], [0, 1, 1, 0], 
    [0, 1, 0, 0], [0, 1, 0, 1], [0, 0, 0, 1], [1, 0, 0, 1] 
]

# --- インデックス配列の定義 ---
FORWARD_INDEXES = [0, 1, 2, 3, 4, 5, 6, 7] 
REVERSE_INDEXES = [7, 6, 5, 4, 3, 2, 1, 0] 

last_step_pattern = [0, 0, 0, 0]


def is_rotating():
    """モーターが現在回転中かどうかを返します。"""
    return _motor_is_rotating

def set_step(step_pattern):
    """4つの制御ピンにステップパターンを適用し、パターンを記録します。"""
    global last_step_pattern
    for i in range(4):
        PINS[i].value(step_pattern[i])
    last_step_pattern = step_pattern

def stop_motor():
    """action: "stop" -> 全てのコイルへの通電を停止し、ドライバーをスリープさせます（省電力）。"""
    global _motor_is_rotating
    print("モーター停止 (通電オフ & nSLEEP LOW)")
    _motor_is_rotating = False # 🚨 状態をリセット
    set_step([0, 0, 0, 0])
    if nSLEEP is not None:
        nSLEEP.value(0) 

def hold_motor():
    """action: "hold" -> 現在の位置または最後に停止した位置のトルクを保持します（コイルに通電）。"""
    print("モーター位置保持 (トルクオン & nSLEEP HIGH)")
    if nSLEEP is not None:
        nSLEEP.value(1) 
    set_step(last_step_pattern) 
    
def reset_motor():
    """action: "reset"/"home" -> ホームポジションへの復帰をシミュレートします。"""
    print("モーター: ホームポジションへ復帰 (シミュレーション)。")
    stop_motor() 

def calculate_steps_from_angle(angle):
    """角度をハーフステップ数に変換します。"""
    steps = int(round(abs(angle) / config.HALF_STEP_ANGLE))
    return steps


def rotate_angle(angle, delay_ms, direction=1, stop_flag=None):
    """
    回転を指示し、必要な情報をグローバル変数にセットします。
    🚨 変更点: この関数自体はすぐにリターンし、ブロッキングしません。
    """
    global _motor_is_rotating, _target_steps, _steps_remaining, _step_delay_ms
    global _direction, _step_sequence_map, _last_step_time, _current_map_index
    
    if abs(angle) < config.HALF_STEP_ANGLE / 2.0:
        print("角度が小さすぎるため回転しません。")
        return False

    if _motor_is_rotating:
        print("Warning: すでに回転中です。新しい回転指示を上書きします。")
        
    if nSLEEP is not None:
        nSLEEP.value(1)
    
    num_steps = calculate_steps_from_angle(angle)
    
    # --- 状態変数の設定 ---
    _motor_is_rotating = True
    _target_steps = num_steps # 総ステップ数
    _steps_remaining = num_steps # 残りステップ数
    _step_delay_ms = int(delay_ms)
    _last_step_time = utime.ticks_ms()
    _direction = direction
    _step_sequence_map = FORWARD_INDEXES if direction == 1 else REVERSE_INDEXES
    _current_map_index = 0 # 常に最初のステップから開始

    print(f"回転指示: 角度={angle}度, 必要ステップ数={num_steps}, 遅延={delay_ms}ms。")
    # 🚨 ここで関数はすぐに終了し、呼び出し元 (effects.py -> main.py) に制御を返します。
    return True

def update_motor(stop_flag=None):
    """
    モーターの状態をチェックし、次のステップを実行します。
    この関数は、main.pyのメインループで頻繁に呼び出される必要があります。
    """
    global _motor_is_rotating, _steps_remaining, _last_step_time, _current_map_index

    if not _motor_is_rotating:
        return

    # --- 強制停止フラグのチェック ---
    if stop_flag and stop_flag[0]:
        print("[MOTOR] 強制停止フラグにより回転を中断。")
        stop_motor()
        return

    # 次のステップを実行する時間が来ているかチェック
    current_time = utime.ticks_ms()
    if utime.ticks_diff(current_time, _last_step_time) >= _step_delay_ms:
        
        # 1. ステップを実行
        seq_index = _step_sequence_map[_current_map_index]
        current_pattern = HALF_STEP_SEQUENCE[seq_index]
        set_step(current_pattern)
        
        # 2. 状態を更新
        _last_step_time = current_time
        _steps_remaining -= 1
        _current_map_index = (_current_map_index + 1) % len(_step_sequence_map)
        
        # 3. 回転完了チェック
        if _steps_remaining <= 0:
            print("回転完了。")
            _motor_is_rotating = False
            # 回転完了後もトルクを保持するため、ここではstop_motorは呼ばない
            
        return
    
    # 時間が来ていない場合は何もしないでリターンし、メインループに制御を返す
    return
