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
            sound_patterns.stop_playback() # 停止処理を有効化
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
                # NEW: グローバルインデックス/ストリップ名指定でLEDを個別に設定
                # 例: ["effect", "global_set", [1, 2, 3], 255, 255, 0]
                # 例: ["effect", "global_set", "LV4", 255, 0, 0]
                indices_or_strip_name = cmd[2]
                r, g, b = cmd[3], cmd[4], cmd[5]

                # led_patterns.py側で文字列（"all"やストリップ名）とリストの両方を受け付けて処理するため、そのまま渡す
                if isinstance(indices_or_strip_name, (list, str)):
                    led_patterns.set_global_leds_by_indices(indices_or_strip_name, r, g, b)
                else:
                    print(f"Error: global_set のインデックスはリストまたは文字列である必要があります: {indices_or_strip_name}")
            
            elif cmd_name == 'fade' and len(cmd) == 6:
                # NEW: フェード処理
                # 例: ["effect", "fade", [0, 1], [0, 0, 0], [255, 0, 0], 1500]
                # 例: ["effect", "fade", "LV4", [0, 0, 0], [255, 0, 0], 1500]
                indices_or_name = cmd[2]
                start_color = cmd[3]
                end_color = cmd[4]
                duration_ms = cmd[5]

                # led_patterns.fade_global_leds はリストを期待するため、ここでインデックスを解決する
                indices = []
                if isinstance(indices_or_name, str):
                    if indices_or_name == "all":
                        indices = list(range(led_patterns.get_total_led_count()))
                    else:
                        indices = led_patterns.get_global_indices_for_strip(indices_or_name)
                elif isinstance(indices_or_name, list):
                    indices = indices_or_name
                
                # 解決されたインデックスリストが空ならエラー
                if not indices:
                    print(f"Error: fade 対象のLEDが特定できません: {indices_or_name}")
                    continue

                # 色と時間の引数チェック
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
                # 従来のローカルストリップ設定 (duration付き)
                # 例: ["effect", "color_set", "LV1", 0, 255, 0, 0, 1000] (durationは7番目の要素)
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
# 抽選対象から、数字以外のキー（例: "__readme" や "_README_"）を除外します。
def playRandomEffect(scenarios_data):
    if not scenarios_data:
        return None, None
    
    # 🌟 修正ポイント: キーが数字のみで構成されているもの（シナリオ番号）のみを対象とする
    valid_keys = [key for key in scenarios_data.keys() if key.isdigit()]
    
    if not valid_keys:
        return None, None

    num = random.choice(valid_keys)
    command_list = scenarios_data[num]
    return num, command_list
