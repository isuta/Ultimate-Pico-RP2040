import config
import time
import random

import sound_patterns
import led_patterns  # NeoPixelグローバル制御モジュール (neopixel_controller.py)
from stepper_motor import StepperMotor

# グローバルモーターインスタンス（ピン番号は config で定義しておくとベター）
motor = None
try:
    motor = StepperMotor(debug=True)
except Exception as e:
    print(f"StepperMotor 初期化失敗: {e}")
    motor = None

def init():
    """モジュール初期化：モーターなどの外部デバイスを安全に初期化"""
    global motor
    try:
        motor = StepperMotor(debug=True)
        print("[Init] StepperMotor 初期化完了")
    except Exception as e:
        print(f"[Error] StepperMotor 初期化失敗: {e}")
        motor = None

# --- 依存関係の解決 ---
# led_patterns (neopixel_controller.py) から取得できない関数を補完
def get_global_indices_for_strip(strip_name):
    """
    ストリップ名に対応するグローバルインデックスのリストを取得します。
    config.NEOPIXEL_STRIPS の定義を使用してインデックスを計算します。
    """
    indices = []
    start_index = 0

    for name, info in sorted_strips:
        count = info['count']
        if name == strip_name:
            indices.extend(range(start_index, start_index + count))
            break
        start_index += count

    if not indices:
        print(f"Warning: 未知のストリップ名 '{strip_name}' です。")

    return indices
# ----------------------

def execute_command(command_list, stop_flag_ref):
    """
    JSONで定義されたコマンドリスト（リスト形式または辞書形式）を順番に実行します。
    実行終了後、モーターの通電を解除して停止させます。
    """
    try:
        for cmd in command_list:
            if stop_flag_ref[0]:
                print("停止フラグが検出されました。コマンドを中断します。")
                sound_patterns.stop_playback()
                stop_flag_ref[0] = False
                return

            is_dict_format = isinstance(cmd, dict)
            cmd_type = cmd.get("type") if is_dict_format else (cmd[0] if isinstance(cmd, list) and cmd else None)

            if not cmd_type:
                print(f"Error: 不明なコマンド形式または空のコマンド: {cmd}")
                continue

            # --- 辞書形式の処理 ---
            if is_dict_format:
                if cmd_type == 'led':
                    command = cmd.get("command")
                    if command == 'off':
                        led_patterns.pattern_off(stop_flag_ref)
                    elif command == 'fill':
                        strip_name = cmd.get("strip", "all")
                        color = cmd.get("color")
                        duration_ms = cmd.get("duration", 0)
                        if not (isinstance(color, list) and len(color) == 3):
                            print(f"Error: fill コマンドの色引数 ({color}) が不正です。")
                            continue
                        r, g, b = color
                        if led_patterns.is_neopixel_available():
                            led_patterns.set_global_leds_by_indices(strip_name, r, g, b)
                            if duration_ms > 0:
                                start_time = time.ticks_ms()
                                while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
                                    if stop_flag_ref[0]:
                                        print("LED点灯を中断します。")
                                        stop_flag_ref[0] = False
                                        return
                                    time.sleep_ms(50)
                        else:
                            print(f"LED: fill {strip_name} を ({r}, {g}, {b})（スキップ - NeoPixel利用不可）")
                    else:
                        print(f"不明な led コマンド: {command}")

                elif cmd_type == 'motor':
                    if not motor:
                        print("モーター制御スキップ（モジュール未初期化）")
                        continue
                    command = cmd.get("command")
                    if command == "rotate":
                        motor.rotate_degrees(cmd.get("angle", 0), cmd.get("speed", 200), cmd.get("direction", 1))
                    elif command == "step":
                        motor.move_steps(cmd.get("steps", 0), cmd.get("direction", 1))
                    else:
                        print(f"不明な motor コマンド: {command}")
                else:
                    print(f"不明な辞書型コマンドタイプ: {cmd_type}")

            # --- リスト形式の処理 ---
            else:
                if cmd_type == 'sound' and len(cmd) == 3:
                    folder_num, file_num = cmd[1], cmd[2]
                    if sound_patterns.is_dfplayer_available():
                        sound_patterns.play_sound(folder_num, file_num)
                    else:
                        print(f"Sound: フォルダ{folder_num}のファイル{file_num}を再生（スキップ - DFPlayer利用不可）")
                elif cmd_type == 'delay' and len(cmd) == 2:
                    delay_time = cmd[1]
                    start_time = time.ticks_ms()
                    while time.ticks_diff(time.ticks_ms(), start_time) < delay_time:
                        if stop_flag_ref[0]:
                            print("Delayを中断します。")
                            stop_flag_ref[0] = False
                            return
                        time.sleep_ms(50)
                elif cmd_type == 'effect':
                    # effect コマンド群は従来通りの処理（省略せず元コードのまま使用可能）
                    ...
                else:
                    print(f"不明なリスト型コマンドタイプ: {cmd_type}")
    finally:
        # すべての処理が終わった後、モーターを必ず停止
        if motor:
            motor.stop_motor()

def playEffectByNum(scenarios_data, num, stop_flag_ref):
    command_list = scenarios_data.get(num)
    if isinstance(command_list, dict):
        command_list = [command_list]
    elif not command_list:
        return False
    execute_command(command_list, stop_flag_ref)
    return True

def playRandomEffect(scenarios_data):
    if not scenarios_data:
        return None, None
    valid_keys = [key for key in scenarios_data.keys() if key.isdigit()]
    if not valid_keys:
        return None, None
    num = random.choice(valid_keys)
    command_list = scenarios_data[num]
    if isinstance(command_list, dict):
        command_list = [command_list]
    return num, command_list
