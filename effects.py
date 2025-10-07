import led_patterns
import sound_patterns
import oled_patterns
import time
import random

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
            color = command.get('color', [0, 0, 0])
            
            if cmd == 'set_color':
                print(f"LED: Set {strip_name} to {color}")
                led_patterns.set_color(strip_name, color)
                
            elif cmd == 'off':
                print(f"LED: Turn off {strip_name}")
                led_patterns.off(strip_name)
                
            elif cmd == 'fade_in':
                # --- 新しい fade_in コマンドの処理 ---
                duration_ms = command.get('duration_ms', 500)  # デフォルト500ms
                print(f"LED: Fade In on {strip_name} to {color} over {duration_ms}ms")
                # led_patternsの新しい関数を呼び出す
                led_patterns.fade_in_color(strip_name, color, duration_ms, stop_flag)
                # -------------------------------------

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
                # oled_patterns.push_message はリストを期待するため、messageをリストで渡す
                oled_patterns.push_message(message)
                
            elif cmd == 'clear':
                print("OLED: Clear screen")
                oled_patterns.clear_display()

        elif cmd_type == 'wait':
            ms = command.get('ms', 100)
            print(f"WAIT: Waiting for {ms}ms")
            # stop_flagをチェックしながら待機するために、短い時間でループ
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < ms:
                if stop_flag[0]:
                    print("Wait interrupted by flag.")
                    break
                time.sleep_ms(10)
        
        else:
            print(f"Warning: Unknown command type or command: {cmd_type}/{cmd}")

    # シナリオ終了時のクリーンアップ
    if stop_flag[0]:
        print("Scenario clean up (Stopped).")
    else:
        print("Scenario finished normally.")
        
    # 再生終了時のクリーンアップ処理
    led_patterns.clear_all()
    # sound_patterns.stop_playback() # スレッド実行中は呼び出しを避ける

def playRandomEffect(scenarios_data):
    """
    ランダムなシナリオを選択して、そのコマンドリストを返します。
    """
    if not scenarios_data:
        return None, []
        
    scenario_keys = list(scenarios_data.keys())
    # 抽選ロジックをここに書く (例: random.choice)
    # 現在は単純にランダムに選択
    
    # 抽選結果の演出（ここではスキップ）
    
    selected_num = random.choice(scenario_keys)
    return selected_num, scenarios_data[selected_num]
