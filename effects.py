import config
import time
import random

import sound_patterns
import led_patterns # 修正後の led_patterns を使用

def execute_command(command_list, stop_flag_ref):
    """
    JSONで定義されたコマンドリストを順番に実行します。
    """
    for cmd in command_list:
        # 実行中に停止フラグが立っていたら、実行を中断し、フラグをリセットして終了
        if stop_flag_ref[0]:
            print("停止フラグが検出されました。コマンドを中断します。")
            # サウンド再生中の場合は停止
            # sound_patterns.stop_playback() # 必要に応じて実装
            stop_flag_ref[0] = False
            return

        cmd_type = cmd[0]
        
        if cmd_type == 'sound':
            # サウンド処理 (sound_patterns.py に委譲)
            # コマンド形式: ["sound", folder_num, file_num]
            if len(cmd) == 3:
                folder_num = cmd[1]
                file_num = cmd[2]
                sound_patterns.play_sound(folder_num, file_num)
            else:
                print(f"Error: 不正な sound コマンド形式: {cmd}")

        elif cmd_type == 'delay':
            # ディレイ処理 (停止フラグを監視しながら待機)
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
        
        # effect コマンドの解釈
        elif cmd_type == 'effect':
            cmd_name = cmd[1]
            
            if cmd_name == 'off' and len(cmd) == 2:
                # 例: ["effect", "off"] の場合 (全消灯)
                led_patterns.pattern_off(stop_flag_ref)
                
            elif cmd_name == 'global_set' and len(cmd) == 6:
                # NEW: グローバルインデックス指定でLEDを個別に設定
                # 例: ["effect", "global_set", [1, 2, 3], 255, 255, 0]
                indices = cmd[2]
                r, g, b = cmd[3], cmd[4], cmd[5]

                if isinstance(indices, list):
                    print(f"LED: グローバルインデックス {indices} を ({r}, {g}, {b}) で設定")
                    led_patterns.set_global_leds_by_indices(indices, r, g, b)
                else:
                    print(f"Error: global_set のインデックスはリストである必要があります: {indices}")
            
            elif cmd_name == 'fade' and len(cmd) == 6:
                # NEW: フェード処理
                # 例: ["effect", "fade", [0, 1], [0, 0, 0], [255, 0, 0], 1500]
                indices = cmd[2]
                start_color = cmd[3]
                end_color = cmd[4]
                duration_ms = cmd[5]

                if isinstance(indices, list) and isinstance(start_color, list) and isinstance(end_color, list) and len(start_color) == 3 and len(end_color) == 3:
                    led_patterns.fade_global_leds(
                        indices, 
                        start_color, 
                        end_color, 
                        duration_ms, 
                        stop_flag_ref
                    )
                else:
                    print(f"Error: fade コマンドの引数が不正です: {cmd}")
                    
            elif len(cmd) == 7:
                # 従来のローカルストリップ設定 (duration付き)
                # 例: ["effect", "color_set", "LV1", 0, 255, 0, 0, 1000] (durationは7番目の要素)
                # 注: コマンド形式の長さが 7 で、cmd[1]がストリップ名 (例: 'LV1') の場合
                strip_name = cmd[1]
                led_index = cmd[2]
                r, g, b = cmd[3], cmd[4], cmd[5]
                duration_ms = cmd[6]
                
                # execute_color_command を呼び出す
                led_patterns.execute_color_command(
                    strip_name, led_index, r, g, b, duration_ms, stop_flag_ref
                )
            else:
                print(f"不明な effect コマンド形式または引数不足: {cmd}")

        else:
            print(f"不明なコマンドタイプ: {cmd_type}")

# デバッグモード用に、指定した番号のエフェクトを実行する関数
def playEffectByNum(scenarios_data, num, stop_flag_ref):
    command_list = scenarios_data.get(num)
    if command_list:
        execute_command(command_list, stop_flag_ref)
        return True
    else:
        return False

# ランダムなエフェクト/サウンドを選び、その抽選番号とコマンドリストを返します。
# 抽選対象から、"__" で始まるキー（例: "__readme"）を除外します。
def playRandomEffect(scenarios_data):
    if not scenarios_data:
        return None, None
    
    # システム設定キーを除外したリストを作成
    valid_keys = [key for key in scenarios_data.keys() if not key.startswith('__')]
    
    if not valid_keys:
        return None, None

    num = random.choice(valid_keys)
    command_list = scenarios_data[num]
    return num, command_list
