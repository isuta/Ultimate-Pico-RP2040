import config
import time
import random

import sound_patterns
import neopixel_controller  # NeoPixelグローバル制御モジュール
import pwm_led_controller   # PWM LED制御モジュール
import servo_rotation_controller     # サーボモーター制御モジュール（連続回転型）
import servo_position_controller  # サーボモーター制御モジュール（角度制御型）
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
            
            # コマンドタイプの判定（辞書形式では "type" キーまたは特定キーで判定）
            if is_dict_format:
                # "type" キーがあれば使用、なければ最初のキーをコマンドタイプとする
                if "type" in cmd:
                    cmd_type = cmd["type"]
                else:
                    # led_on, led_off, led_fade_in, led_fade_out, wait_ms, stop_playback など
                    cmd_type = next(iter(cmd.keys())) if cmd else None
            else:
                cmd_type = cmd[0] if isinstance(cmd, list) and cmd else None

            if not cmd_type:
                print(f"[Warning] Unknown command format or empty command: {cmd}")
                continue

            try:
                # --- 辞書形式の処理 ---
                if is_dict_format:
                    # PWM LED制御コマンド（旧形式）
                    if 'led_on' in cmd:
                        params = cmd['led_on']
                        led_index = params.get('led_index', 0)
                        brightness = params.get('max_brightness', 100)
                        if pwm_led_controller.is_pwm_led_available():
                            pwm_led_controller.set_brightness(led_index, brightness)
                        else:
                            print(f"PWM LED: LED #{led_index} 点灯（スキップ - PWM LED利用不可）")
                    
                    elif 'led_off' in cmd:
                        params = cmd['led_off']
                        led_index = params.get('led_index', 0)
                        if pwm_led_controller.is_pwm_led_available():
                            pwm_led_controller.set_brightness(led_index, 0)
                        else:
                            print(f"PWM LED: LED #{led_index} 消灯（スキップ - PWM LED利用不可）")
                    
                    elif 'led_fade_in' in cmd:
                        params = cmd['led_fade_in']
                        led_index = params.get('led_index', 0)
                        duration_ms = params.get('duration_ms', 0)
                        brightness = params.get('max_brightness', 100)
                        if pwm_led_controller.is_pwm_led_available():
                            pwm_led_controller.fade_pwm_led(led_index, brightness, duration_ms, stop_flag_ref)
                        else:
                            print(f"PWM LED: LED #{led_index} フェードイン（スキップ - PWM LED利用不可）")
                    
                    elif 'led_fade_out' in cmd:
                        params = cmd['led_fade_out']
                        led_index = params.get('led_index', 0)
                        duration_ms = params.get('duration_ms', 0)
                        if pwm_led_controller.is_pwm_led_available():
                            pwm_led_controller.fade_pwm_led(led_index, 0, duration_ms, stop_flag_ref)
                        else:
                            print(f"PWM LED: LED #{led_index} フェードアウト（スキップ - PWM LED利用不可）")
                    
                    elif 'wait_ms' in cmd:
                        duration_ms = cmd['wait_ms']
                        if duration_ms < 0:
                            print(f"[Warning] Negative wait time ignored: {duration_ms}")
                            continue
                        start_time = time.ticks_ms()
                        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
                            if stop_flag_ref[0]:
                                print("Wait中断します。")
                                stop_flag_ref[0] = False
                                return
                            time.sleep_ms(50)
                    
                    elif 'stop_playback' in cmd:
                        print("全モジュール停止コマンドを実行します。")
                        try:
                            sound_patterns.stop_playback()
                        except Exception as e:
                            print(f"[Warning] Sound stop failed: {e}")
                        try:
                            pwm_led_controller.all_off()
                        except Exception as e:
                            print(f"[Warning] PWM LED stop failed: {e}")
                        try:
                            neopixel_controller.pattern_off(stop_flag_ref)
                        except Exception as e:
                            print(f"[Warning] NeoPixel stop failed: {e}")
                    
                    # NeoPixel LED制御コマンド（辞書形式）
                    elif cmd_type == 'led':
                        command = cmd.get("command")
                        if command == 'off':
                            neopixel_controller.pattern_off(stop_flag_ref)
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
                            if neopixel_controller.is_neopixel_available():
                                neopixel_controller.set_global_leds_by_indices(strip_name, r, g, b)
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
                    
                    elif cmd_type == 'servo':
                        # サーボモーター制御（連続回転型/角度制御型を自動判別）
                        command = cmd.get("command")
                        servo_index = cmd.get("servo_index", 0)
                        
                        # config.pyからサーボタイプを取得
                        servo_types = getattr(config, 'SERVO_TYPES', [])
                        if servo_index >= len(servo_types):
                            print(f"[Warning] Servo #{servo_index} not configured in SERVO_TYPES")
                            continue
                        
                        servo_type = servo_types[servo_index]
                        
                        # タイプに応じて適切なコントローラーに振り分け
                        if servo_type == 'continuous':
                            # 連続回転型サーボ
                            if not servo_rotation_controller.is_servo_available():
                                print("サーボ制御スキップ（連続回転型なし）")
                                continue
                            
                            if command == "rotate":
                                speed = cmd.get("speed", 0)  # -100～100
                                duration_ms = cmd.get("duration_ms", 0)
                                print(f"[Servo] Rotate servo #{servo_index}, speed={speed}, duration={duration_ms}ms")
                                
                                if duration_ms > 0:
                                    # 時間指定回転（ブロッキング、stop_flag対応）
                                    print(f"[Servo] Starting timed rotation...")
                                    servo_rotation_controller.rotate_timed(servo_index, speed, duration_ms, stop_flag_ref)
                                    print(f"[Servo] Timed rotation completed")
                                else:
                                    # 継続回転（ノンブロッキング）
                                    servo_rotation_controller.set_speed(servo_index, speed)
                            
                            elif command == "stop":
                                servo_rotation_controller.stop(servo_index)
                            
                            elif command == "stop_all":
                                servo_rotation_controller.stop_all()
                            
                            else:
                                print(f"[Warning] Unknown continuous servo command: {command}")
                        
                        elif servo_type == 'position':
                            # 角度制御型サーボ
                            if not servo_position_controller.is_servo_available():
                                print("サーボ角度制御スキップ（角度制御型なし）")
                                continue
                            
                            if command == "move":
                                angle = cmd.get("angle", 90)  # 0～180度
                                duration_ms = cmd.get("duration_ms", 0)
                                
                                if duration_ms > 0:
                                    # 時間指定保持（ブロッキング、stop_flag対応）
                                    servo_position_controller.move_angle_timed(servo_index, angle, duration_ms, stop_flag_ref)
                                else:
                                    # 角度設定のみ（ノンブロッキング）
                                    servo_position_controller.set_angle(servo_index, angle)
                            
                            elif command == "center":
                                servo_position_controller.center(servo_index)
                            
                            elif command == "center_all":
                                servo_position_controller.center_all()
                            
                            else:
                                print(f"[Warning] Unknown position servo command: {command}")
                        
                        else:
                            print(f"[Warning] Unknown servo type '{servo_type}' for servo #{servo_index}")
                    
                    elif cmd_type == 'motor':
                        # ステッピングモーター制御（既存）
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
                    
                    elif cmd_type == 'delay':
                        # {"type": "delay", "duration": 1000}
                        duration_ms = cmd.get("duration", 0)
                        if duration_ms < 0:
                            print(f"[Warning] Negative delay time ignored: {duration_ms}")
                            continue
                        start_time = time.ticks_ms()
                        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
                            if stop_flag_ref[0]:
                                print("Delayを中断します。")
                                stop_flag_ref[0] = False
                                return
                            time.sleep_ms(50)
                    
                    elif cmd_type == 'sound':
                        # {"type": "sound", "folder": 2, "file": 1}
                        folder_num = cmd.get("folder")
                        file_num = cmd.get("file")
                        if folder_num is None or file_num is None:
                            print(f"[Data Error] folder and file required for sound command.")
                            continue
                        if sound_patterns.is_dfplayer_available():
                            sound_patterns.play_sound(folder_num, file_num)
                        else:
                            print(f"Sound: フォルダ{folder_num}のファイル{file_num}を再生（スキップ - DFPlayer利用不可）")
                    
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
                        # NeoPixel効果コマンド ["effect", "fade", indices, start_color, end_color, duration]
                        if len(cmd) < 2:
                            print(f"[Warning] Invalid effect command: {cmd}")
                            continue
                        
                        effect_type = cmd[1]
                        
                        if effect_type == 'fade' and len(cmd) == 6:
                            # ["effect", "fade", indices_or_strip, [r,g,b], [r,g,b], duration_ms]
                            indices_or_strip = cmd[2]
                            start_color = cmd[3]
                            end_color = cmd[4]
                            duration_ms = cmd[5]
                            
                            if not (isinstance(start_color, list) and len(start_color) == 3):
                                print(f"[Data Error] Invalid start_color in fade command.")
                                continue
                            if not (isinstance(end_color, list) and len(end_color) == 3):
                                print(f"[Data Error] Invalid end_color in fade command.")
                                continue
                            
                            if neopixel_controller.is_neopixel_available():
                                # インデックスリストまたはストリップ名を解決
                                if isinstance(indices_or_strip, str):
                                    if indices_or_strip == "all":
                                        indices = list(range(neopixel_controller.get_total_led_count()))
                                    else:
                                        indices = neopixel_controller.get_global_indices_for_strip(indices_or_strip)
                                elif isinstance(indices_or_strip, list):
                                    indices = indices_or_strip
                                else:
                                    print(f"[Data Error] Invalid indices format: {indices_or_strip}")
                                    continue
                                
                                # 共通フェード処理を使用（内部実装で fade_controller を使用）
                                neopixel_controller.fade_global_leds(indices, start_color, end_color, duration_ms, stop_flag_ref)
                            else:
                                print(f"LED: fade （スキップ - NeoPixel利用不可）")
                        
                        elif effect_type == 'global_set' and len(cmd) >= 5:
                            # ["effect", "global_set", indices_or_strip, r, g, b]
                            indices_or_strip = cmd[2]
                            r, g, b = cmd[3], cmd[4], cmd[5]
                            
                            if not all(isinstance(c, int) and 0 <= c <= 255 for c in [r, g, b]):
                                print(f"[Data Error] Invalid color values: ({r}, {g}, {b})")
                                continue
                            
                            if neopixel_controller.is_neopixel_available():
                                neopixel_controller.set_global_leds_by_indices(indices_or_strip, r, g, b)
                            else:
                                print(f"LED: global_set （スキップ - NeoPixel利用不可）")
                        
                        elif effect_type == 'off':
                            # ["effect", "off"]
                            neopixel_controller.pattern_off(stop_flag_ref)
                        
                        else:
                            print(f"[Warning] Unknown effect type: {effect_type}")
                    
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
