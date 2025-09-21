# effects.py
import config
import machine
import time
import random
from neopixel import NeoPixel

# sound_patternsモジュールをインポート
import sound_patterns
import led_patterns

# 停止フラグを引数として受け取るように変更
def execute_command(command_list, stop_flag_ref):
    for cmd in command_list:
        if stop_flag_ref[0]:
            print("停止フラグが検出されました。コマンドを中断します。")
            # DFPlayerの停止コマンドをsound_patternsに任せる
            sound_patterns.stop_playback() 
            stop_flag_ref[0] = False
            return

        cmd_type = cmd[0]
        
        if cmd_type == 'sound':
            folder_num = cmd[1]
            file_num = cmd[2]
            # sound_patternsモジュールの関数を呼び出す
            sound_patterns.play_sound(folder_num, file_num)
        elif cmd_type == 'effect':
            pattern_name = cmd[1]
            # led_patternsモジュールのパターンを呼び出す
            if pattern_name in led_patterns.effect_patterns:
                led_patterns.effect_patterns[pattern_name](stop_flag_ref)
        elif cmd_type == 'delay':
            delay_time = cmd[1]
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < delay_time:
                if stop_flag_ref[0]:
                    print("Delayを中断します。")
                    stop_flag_ref[0] = False
                    return
                time.sleep_ms(50)
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
