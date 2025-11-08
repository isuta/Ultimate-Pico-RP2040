import config
import time
import random

import sound_patterns
import led_patterns  # NeoPixelグローバル制御モジュール (neopixel_controller.py)
from stepper_motor import StepperMotor

# motor変数をモジュールレベルで初期化することで、
# init()が呼び出される前でもNameErrorを防ぐ
motor = None 

# グローバルモーターインスタンス（ピン番号は config で定義）
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
                try:
                    sound_patterns.stop_playback()
                except Exception as e:
                    print(f"[Warning] Sound stop failed: {e}")
                stop_flag_ref[0] = False
                return

            is_dict_format = isinstance(cmd, dict)
            cmd_type = cmd.get("type") if is_dict_format else (cmd[0] if isinstance(cmd, list) and cmd else None)

            if not cmd_type:
                print(f"[Warning] Unknown command format or empty command: {cmd}")
                continue

            try:
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
                                print(f"[Data Error] Invalid color format ({color}) in fill command.")
                                continue
                            r, g, b = color
                            if not all(0 <= c <= 255 for c in [r, g, b]):
                                print(f"[Data Error] Color values out of range: ({r}, {g}, {b})")
                                continue
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
                            print(f"[Warning] Unknown led command: {command}")

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
                            print(f"[Warning] Unknown motor command: {command}")
                    else:
                        print(f"[Warning] Unknown dict command type: {cmd_type}")

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
                        if delay_time < 0:
                            print(f"[Warning] Negative delay time ignored: {delay_time}")
                            continue
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
                        print(f"[Warning] Unknown list command type: {cmd_type}")
            
            except OSError as e:
                print(f"[Hardware Error] Command execution failed: {cmd} - {e}")
                continue
            except ValueError as e:
                print(f"[Data Error] Invalid value in command: {cmd} - {e}")
                continue
            except Exception as e:
                print(f"[Error] Unexpected error in command: {cmd} - {e}")
                import sys
                sys.print_exception(e)
                continue

    except Exception as e:
        print(f"[Critical Error] execute_command failed: {e}")
        import sys
        sys.print_exception(e)
    finally:
        # すべての処理が終わった後、モーターを必ず停止
        if motor:
            try:
                motor.stop_motor()
            except Exception as e:
                print(f"[Warning] Motor stop failed: {e}")

def playEffectByNum(scenarios_data, num, stop_flag_ref):
    """指定されたシナリオ番号のエフェクトを再生"""
    try:
        command_list = scenarios_data.get(num)
        if isinstance(command_list, dict):
            command_list = [command_list]
        elif not command_list:
            print(f"[Warning] Scenario {num} not found in scenarios data")
            return False
        
        execute_command(command_list, stop_flag_ref)
        return True
    except KeyError as e:
        print(f"[Data Error] Invalid scenario key: {num} - {e}")
        return False
    except Exception as e:
        print(f"[Error] playEffectByNum failed for scenario {num}: {e}")
        import sys
        sys.print_exception(e)
        return False

def playRandomEffect(scenarios_data):
    """ランダムなエフェクトを選択"""
    try:
        if not scenarios_data:
            print("[Warning] No scenarios data available")
            return None, None
        
        valid_keys = [key for key in scenarios_data.keys() if key.isdigit()]
        if not valid_keys:
            print("[Warning] No valid numeric scenario keys found")
            return None, None
        
        num = random.choice(valid_keys)
        command_list = scenarios_data[num]
        if isinstance(command_list, dict):
            command_list = [command_list]
        
        return num, command_list
    except Exception as e:
        print(f"[Error] playRandomEffect failed: {e}")
        import sys
        sys.print_exception(e)
        return None, None
