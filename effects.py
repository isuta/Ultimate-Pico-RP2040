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
            folder_num = cmd[1]
            file_num = cmd[2]
            sound_patterns.play_sound(folder_num, file_num)
            pass
        elif cmd_type == 'delay':
            # ディレイ処理 (停止フラグを監視しながら待機)
            delay_time = cmd[1]
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < delay_time:
                if stop_flag_ref[0]:
                    print("Delayを中断します。")
                    stop_flag_ref[0] = False
                    return
                time.sleep_ms(50)
            pass
        
        # effect コマンドの解釈
        elif cmd_type == 'effect':
            if len(cmd) == 2 and cmd[1] == 'off':
                # 例: ["effect", "off"] の場合 (全消灯)
                led_patterns.pattern_off(stop_flag_ref)
            elif len(cmd) == 7:
                # 例: ["effect", "LV1", 0, 255, 0, 0, 1000] の場合 (データ駆動パターン)
                strip_name = cmd[1]
                led_index = cmd[2]
                r, g, b = cmd[3], cmd[4], cmd[5]
                duration_ms = cmd[6]
                
                # execute_color_command を呼び出す
                led_patterns.execute_color_command(
                    strip_name, led_index, r, g, b, duration_ms, stop_flag_ref
                )
            else:
                print(f"不明な effect コマンド形式: {cmd}")
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
def playRandomEffect(scenarios_data):
    if not scenarios_data:
        return None, None
    num = random.choice(list(scenarios_data.keys()))
    command_list = scenarios_data[num]
    return num, command_list
