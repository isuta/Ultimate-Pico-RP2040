import led_patterns
import sound_patterns
import oled_patterns
import time
import random
import config 

def _get_color(color_setting):
    """
    JSONからの色設定 (リスト [R, G, B] または文字列 'RED' など) を受け取り、
    RGBリスト [R, G, B] に変換して返します。
    """
    # 文字列の場合 (色名)
    if isinstance(color_setting, str):
        # 大文字に変換して検索し、見つからなければBLACK [0, 0, 0] を返す
        return config.COLOR_PALETTE.get(color_setting.upper(), [0, 0, 0])
    
    # リストの場合 ([R, G, B])
    if isinstance(color_setting, list) and len(color_setting) == 3:
        return color_setting
        
    # それ以外はデフォルトでBLACK [0, 0, 0] を返す
    return [0, 0, 0]


def playEffectByNum(scenarios_data, scenario_num, stop_flag):
    """
    scenarios_dataから指定されたシナリオ番号のエフェクトを実行します。
    """
    if stop_flag[0]: # 実行開始前のチェック
        stop_flag[0] = False
        return

    command_list = scenarios_data.get(scenario_num, [])
    if not command_list:
        print(f"Scenario {scenario_num} not found or empty.")
        return

    print(f"--- Executing Scenario {scenario_num} ---")

    # シナリオ実行中のフラグをリセット
    stop_flag[0] = False

    for command in command_list:
        if stop_flag[0]:
            print("Scenario execution stopped by flag.")
            break
        
        cmd_type = command.get('type')
        cmd = command.get('cmd')

        if cmd_type == 'led':
            strip_name = command['strip']
            
            # --- 色名/RGBリストの変換処理 ---
            color_setting = command.get('color', 'BLACK')
            color = _get_color(color_setting)
            # --------------------------
            
            if cmd == 'set_color':
                # colorはRGBリスト
                print(f"LED: Set {strip_name} to {color_setting}/{color}")
                led_patterns.set_color(strip_name, color)
                
            elif cmd == 'off':
                print(f"LED: Turn off {strip_name}")
                led_patterns.off(strip_name)
                
            elif cmd == 'fade_in':
                duration_ms = command.get('duration_ms', 500)
                print(f"LED: Fade In on {strip_name} to {color_setting}/{color} over {duration_ms}ms")
                led_patterns.fade_in_color(strip_name, color, duration_ms, stop_flag)
                
            elif cmd == 'fade_out':
                duration_ms = command.get('duration_ms', 500)
                print(f"LED: Fade Out on {strip_name} from {color_setting}/{color} over {duration_ms}ms")
                led_patterns.fade_out_color(strip_name, color, duration_ms, stop_flag)

            elif cmd == 'blink':
                duration_ms = command.get('duration_ms', 1000)
                half_duration = duration_ms // 2
                print(f"LED: Blink on {strip_name} to {color_setting}/{color} over {duration_ms}ms (In:{half_duration}ms, Out:{half_duration}ms)")

                led_patterns.fade_in_color(strip_name, color, half_duration, stop_flag)
                
                if stop_flag[0]:
                    print("Blink interrupted after Fade In.")
                    continue

                led_patterns.fade_out_color(strip_name, color, half_duration, stop_flag)
                
            elif cmd == 'set_pixel':
                index = command.get('index')
                if index is not None and isinstance(index, int):
                    print(f"LED: Set Pixel {index} on {strip_name} to {color_setting}/{color}")
                    led_patterns.set_pixel_color(strip_name, index, color)
                else:
                    print("Error: 'set_pixel' requires valid integer 'index'.")

        elif cmd_type == 'sound':
            if cmd == 'play':
                folder = command['folder']
                file = command['file']
                print(f"SOUND: Play folder {folder}, file {file}")
                sound_patterns.play_sound(folder, file)
                
            elif cmd == 'stop':
                print("SOUND: Stop playback")
                sound_patterns.stop_playback()

        elif cmd_type == 'oled':
            if cmd == 'display':
                message = command['message']
                print(f"OLED: Display message: {message}")
                oled_patterns.push_message(message)
                
            elif cmd == 'clear':
                print("OLED: Clear screen")
                oled_patterns.clear_display()

        elif cmd_type == 'wait':
            ms = command.get('ms', 100)
            print(f"WAIT: Waiting for {ms}ms")
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < ms:
                if stop_flag[0]:
                    print("Wait interrupted by flag.")
                    break
                time.sleep_ms(10)
        
        else:
            print(f"Warning: Unknown command type or command: {cmd_type}/{cmd}")

    if stop_flag[0]:
        print("Scenario clean up (Stopped).")
    else:
        print("Scenario finished normally.")
        
    led_patterns.clear_all()

def playRandomEffect(scenarios_data):
    """
    ランダムなシナリオを選択して、そのコマンドリストを返します。
    特殊なキー（_で始まるもの）はランダム再生から除外されます。
    """
    if not scenarios_data:
        return None, []
        
    # 数字のみをランダム再生の対象とする
    scenario_keys = [k for k in scenarios_data.keys() if k.isdigit()]
    
    if not scenario_keys:
        return None, []
        
    selected_num = random.choice(scenario_keys)
    return selected_num, scenarios_data[selected_num]
