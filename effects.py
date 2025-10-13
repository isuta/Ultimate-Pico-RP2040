import config
import time
import random

import sound_patterns
import led_patterns # NeoPixelグローバル制御モジュール (neopixel_controller.py)

# --- 依存関係の解決 ---
# led_patterns (neopixel_controller.py) から取得できない関数を補完
def get_global_indices_for_strip(strip_name):
    """
    ストリップ名に対応するグローバルインデックスのリストを取得します。
    config.NEOPIXEL_STRIPS の定義を使用してインデックスを計算します。
    """
    indices = []
    start_index = 0
    
    # config.NEOPIXEL_STRIPS の定義順序を維持して処理
    sorted_strips = sorted(config.NEOPIXEL_STRIPS.items())
    
    for name, info in sorted_strips:
        count = info['count']
        if name == strip_name:
            # 該当ストリップのインデックス範囲をリストに追加
            indices.extend(range(start_index, start_index + count))
            break # 見つかったら終了
        start_index += count
        
    if not indices:
        print(f"Warning: 未知のストリップ名 '{strip_name}' です。")

    return indices
# ----------------------


def execute_command(command_list, stop_flag_ref):
    """
    JSONで定義されたコマンドリスト（リスト形式または辞書形式）を順番に実行します。
    """
    for cmd in command_list:
        # 実行中に停止フラグが立っていたら、実行を中断し、フラグをリセットして終了
        if stop_flag_ref[0]:
            print("停止フラグが検出されました。コマンドを中断します。")
            sound_patterns.stop_playback()
            stop_flag_ref[0] = False
            return

        cmd_type = None
        is_dict_format = isinstance(cmd, dict)

        # 1. コマンドタイプを決定
        if is_dict_format:
            cmd_type = cmd.get("type")
        elif isinstance(cmd, list) and len(cmd) > 0:
            cmd_type = cmd[0]
        else:
            print(f"Error: 不明なコマンド形式または空のコマンド: {cmd}")
            continue

        
        # --- 新しい辞書形式のコマンド処理 (type: "led" など) ---
        if is_dict_format:
            if cmd_type == 'led':
                # コマンド形式: {"type": "led", "command": "fill", "strip": "LV1", "color": [255, 255, 255], "duration": 3000}
                command = cmd.get("command")
                
                if command == 'off':
                    led_patterns.pattern_off(stop_flag_ref)
                
                elif command == 'fill':
                    strip_name = cmd.get("strip", "all") 
                    color = cmd.get("color")
                    duration_ms = cmd.get("duration", 0)

                    if color is None or not isinstance(color, list) or len(color) != 3:
                        print(f"Error: fill コマンドの色引数 ({color}) が不正です。")
                        continue
                    
                    r, g, b = color[0], color[1], color[2]
                    
                    # 色を設定
                    led_patterns.set_global_leds_by_indices(strip_name, r, g, b)
                    
                    # duration が指定されている場合は待機
                    if duration_ms > 0:
                        start_time = time.ticks_ms()
                        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
                            if stop_flag_ref[0]:
                                print("LED点灯を中断します。")
                                stop_flag_ref[0] = False
                                return
                            time.sleep_ms(50)
                
                # TODO: 今後、辞書形式の 'fade' コマンドなどを追加する場合はここに追加
                else:
                    print(f"不明な led コマンド: {command}")
            
            else:
                # 'led' 以外の辞書型コマンドが今後増えた場合に対応
                print(f"不明な辞書型コマンドタイプ: {cmd_type}")

        # --- 従来のリスト形式のコマンド処理 (type: "sound", "delay", "effect") ---
        else: # is_dict_format が False (つまりリスト形式) の場合のみ実行
            if cmd_type == 'sound':
                # コマンド形式: ["sound", folder_num, file_num]
                if len(cmd) == 3:
                    # ここで cmd はリストであることが確定している
                    folder_num = cmd[1]
                    file_num = cmd[2]
                    sound_patterns.play_sound(folder_num, file_num)
                else:
                    print(f"Error: 不正な sound コマンド形式: {cmd}")

            elif cmd_type == 'delay':
                # コマンド形式: ["delay", duration_ms]
                if len(cmd) == 2:
                    delay_time = cmd[1]
                    start_time = time.ticks_ms()
                    while time.ticks_diff(time.ticks_ms(), start_time) < delay_time:
                        if stop_flag_ref[0]:
                            print("Delayを中断します。")
                            stop_flag_ref[0] = False
                            return
                        time.sleep_ms(50)
                else:
                    print(f"Error: 不正な delay コマンド形式: {cmd}")
            
            elif cmd_type == 'effect':
                # 従来の 'effect' コマンド群 (fade, global_set, color_setを含む)
                if len(cmd) >= 2:
                    cmd_name = cmd[1]
                    
                    if cmd_name == 'off' and len(cmd) == 2:
                        # 例: ["effect", "off"] の場合 (全消灯)
                        led_patterns.pattern_off(stop_flag_ref)
                        
                    elif cmd_name == 'global_set' and len(cmd) == 6:
                        # 例: ["effect", "global_set", "LV4", 255, 0, 0]
                        indices_or_strip_name = cmd[2]
                        r, g, b = cmd[3], cmd[4], cmd[5]

                        if isinstance(indices_or_strip_name, (list, str)):
                            led_patterns.set_global_leds_by_indices(indices_or_strip_name, r, g, b)
                        else:
                            print(f"Error: global_set のインデックスはリストまたは文字列である必要があります: {indices_or_strip_name}")
                            
                    elif cmd_name == 'fade' and len(cmd) == 6:
                        # 例: ["effect", "fade", "LV4", [0, 0, 0], [255, 0, 0], 1500]
                        indices_or_name = cmd[2]
                        start_color = cmd[3]
                        end_color = cmd[4]
                        duration_ms = cmd[5]

                        indices = []
                        if isinstance(indices_or_name, str):
                            if indices_or_name.lower() == "all":
                                indices = list(range(led_patterns.get_total_led_count()))
                            else:
                                indices = get_global_indices_for_strip(indices_or_name)
                        elif isinstance(indices_or_name, list):
                            indices = indices_or_name
                        
                        if not indices:
                            print(f"Error: fade 対象のLEDが特定できません: {indices_or_name}")
                            continue

                        if isinstance(start_color, list) and isinstance(end_color, list) and len(start_color) == 3 and len(end_color) == 3:
                            led_patterns.fade_global_leds(
                                indices, 
                                start_color, 
                                end_color, 
                                duration_ms, 
                                stop_flag_ref
                            )
                        else:
                            print(f"Error: fade コマンドの引数(色または時間)が不正です: {cmd}")
                            
                    elif len(cmd) == 7:
                        # 従来の古いローカルストリップ設定: ["effect", strip_name, led_index, R, G, B, duration_ms]
                        strip_name = cmd[1]
                        led_index = cmd[2]
                        r, g, b = cmd[3], cmd[4], cmd[5]
                        duration_ms = cmd[6]
                        
                        led_patterns.execute_color_command(
                            strip_name, led_index, r, g, b, duration_ms, stop_flag_ref
                        )
                    else:
                        print(f"不明な effect コマンド形式または引数不足: {cmd}")
                else:
                        print(f"不明な effect コマンド形式: {cmd}")

            else:
                print(f"不明なリスト型コマンドタイプ: {cmd_type}")


# デバッグモード用に、指定した番号のエフェクトを実行する関数
def playEffectByNum(scenarios_data, num, stop_flag_ref):
    command_list = scenarios_data.get(num)
    
    # ここで command_list がリストでない場合 (単一の辞書や None の場合) をハンドル
    if isinstance(command_list, dict):
        # 単一のコマンド辞書が渡された場合、リストにラップする (互換性のため)
        command_list = [command_list]
    elif not command_list:
        return False

    execute_command(command_list, stop_flag_ref)
    return True

# ランダムなエフェクト/サウンドを選び、その抽選番号とコマンドリストを返します。
# 抽選対象から、数字以外のキー（例: "__readme" や "_README_"）を除外します。
def playRandomEffect(scenarios_data):
    if not scenarios_data:
        return None, None
    
    # 🌟 キーが数字のみで構成されているもの（シナリオ番号）のみを対象とする
    valid_keys = [key for key in scenarios_data.keys() if key.isdigit()]
    
    if not valid_keys:
        return None, None

    num = random.choice(valid_keys)
    command_list = scenarios_data[num]
    
    if isinstance(command_list, dict):
        # 単一のコマンド辞書が渡された場合、リストにラップする
        command_list = [command_list]
        
    return num, command_list
