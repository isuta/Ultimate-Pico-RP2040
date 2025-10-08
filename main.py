import config
from machine import Pin, ADC # ADCを追加
import time
import random
import json # jsonモジュールをインポート
import _thread # マルチスレッド処理のためにインポート

# モジュールをインポート
import sound_patterns
import effects
import oled_patterns
import led_patterns

# 入力用のプルダウン抵抗を使用するピンとして設定。
button = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

# 3. ボリュームポテンショメータ初期化 (追加)
# config.pyで定義されたピンを使用
volume_pot = ADC(config.VOLUME_POT_PIN)

# 初期待ち
time.sleep(2.0)

# JSONファイルを読み込む関数
def load_scenarios(filename):
    """
    指定されたJSONファイルからシナリオデータを読み込みます。
    数字キーを整数に、それ以外（特殊キー）を文字列のまま保持します。
    """
    with open(filename, 'r') as f:
        scenarios = json.load(f)
    
    # キーを処理: 数字なら整数に、それ以外は文字列のまま
    processed_scenarios = {}
    for k, v in scenarios.items():
        if k.isdigit():
            processed_scenarios[int(k)] = v
        else:
            processed_scenarios[k] = v
    return processed_scenarios

# 初期化
button_pressed = False
press_time = 0
release_time = 0
selected_scenario = 1
last_press_time = 0  # 最後にボタンが押された時間を記録
select_mode = False  # セレクトモード判定
current_display = "" # 現在表示されている文字列を保持
push_message = "Push the button" # ボタンを押してもらうために表示する文字列
select_mode_message = "Select Mode" # セレクトモードのときに表示する文字列
click_count = 0  # 連続短押しカウント
last_click_time = 0 # 前回の短押しが離された時間

# 停止フラグの定義（リストにすることで参照渡しを実現）
stop_flag = [False]
# シナリオ実行中かどうかのフラグ
is_playing = False

# シナリオデータを読み込み
try:
    scenarios_data = load_scenarios('scenarios.json')
except Exception as e:
    print(f"Error loading scenarios: {e}")
    scenarios_data = {}
    select_mode_message = "File Error"

# 初期化と起動表示
oled_patterns.init_oled()

# --- 修正箇所: show_display を push_message に変更 ---
oled_patterns.push_message(['Loading...']) # ロード中表示
led_patterns.init_neopixels()  # NeoPixelの初期化
sound_patterns.init_dfplayer()
time.sleep(2)
oled_patterns.push_message(['Init End']) # 初期化完了表示
# ----------------------------------------------------

# ----------------------------------------------------
# 【起動時デモ/テストモードの実行】(追加)
# ランダム再生の対象外である特殊シナリオを直接呼び出します
print("--- Running Startup Test Scenario ---")
oled_patterns.push_message(["Startup Test", "Color Cycle"])

# 特殊キーを指定して実行（完了までブロックする）
effects.playEffectByNum(scenarios_data, "_TEST_COLOR_CYCLE", stop_flag)

# テスト完了後の表示
oled_patterns.push_message(['Test End'])
time.sleep(1)
# ----------------------------------------------------

if button.value() == 1:
    # 意図しない誤作動を防ぐため、少し待機（チャタリング対策）
    time.sleep(0.05)
    
    start_time = time.ticks_ms()
    # ボタンが押されている間、ループを継続
    while button.value() == 1:
        # 1秒（1000ミリ秒）以上経過したらデバッグモードに移行
        if time.ticks_diff(time.ticks_ms(), start_time) > 1000:
            select_mode = True
            time.sleep(1) # ボタンが離されるのを待つ
            break

# 最初の表示を一度だけ行う
if select_mode:
    current_display = select_mode_message
else:
    current_display = push_message

# --- 修正箇所: show_display を push_message に変更 ---
oled_patterns.push_message([current_display])
# ----------------------------------------------------

# シナリオ再生をスレッドで実行するためのラッパー関数
def play_scenario_in_thread(data, num, flag, callback):
    """
    シナリオをスレッド内で実行し、完了後にコールバックを呼び出す。
    """
    effects.playEffectByNum(data, num, flag)
    callback()

def play_complete_callback():
    """
    シナリオ再生完了時に実行されるコールバック関数。
    """
    global is_playing
    is_playing = False
    print("再生スレッドが終了しました。")

# ボタン入力待ちループ
while True:
    # --- A. ボリューム調整 (追加) ---
    # 16bit (0-65535) -> 30段階 (0-30)にマッピング
    pot_value = volume_pot.read_u16()
    new_volume = int(pot_value * 30 / 65535)
    sound_patterns.set_volume(new_volume)
    # -----------------------------
    
    if select_mode:
        current_button_value = button.value()
        current_time = time.ticks_ms()

        # デバウンス処理
        if time.ticks_diff(current_time, last_press_time) < 300:
            time.sleep_ms(50) # スレッドが解放されるよう少し待機
            continue
        
        # ボタンが押されている場合
        if current_button_value == 1:
            # 押された瞬間を検知
            if not button_pressed:
                button_pressed = True
                press_time = current_time

            # 押下時間が1秒を超えたら長押しと判定
            if not is_playing and time.ticks_diff(current_time, press_time) >= 1000:
                print("長押し（実行開始）")
                is_playing = True
                
                # シナリオ実行をスレッドで開始
                _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, selected_scenario, stop_flag, play_complete_callback))

                new_display = f"Executing: {selected_scenario}"
                if new_display != current_display:
                    # --- 修正箇所: show_display を push_message に変更 ---
                    oled_patterns.push_message([new_display])
                    # ----------------------------------------------------
                    current_display = new_display
                
                # 再生開始後は、ボタンが離されるのを待ってループを続ける
                while button.value() == 1:
                    time.sleep(0.1)
                button_pressed = False
                last_press_time = time.ticks_ms()
                
                # 再生がスレッドで動いているため、すぐに表示を戻す
                new_display = select_mode_message
                if new_display != current_display:
                    # --- 修正箇所: show_display を push_message に変更 ---
                    oled_patterns.push_message([new_display])
                    # ----------------------------------------------------
                    current_display = new_display

        # ボタンが離された場合
        elif button_pressed and current_button_value == 0:
            press_duration = time.ticks_diff(current_time, press_time)
            
            # 再生中に短押しを検知した場合
            if is_playing and press_duration < 500:
                print("短押しによる停止を検知")
                stop_flag[0] = True
                # is_playing フラグは再生スレッドの終了時にリセットされる
                button_pressed = False
                last_press_time = time.ticks_ms()
                new_display = select_mode_message
                if new_display != current_display:
                    # --- 修正箇所: show_display を push_message に変更 ---
                    oled_patterns.push_message([new_display])
                    # ----------------------------------------------------
                    current_display = new_display

            # 再生中でない場合の短押し（選択動作）
            elif not is_playing and press_duration < 500:
                # 短押しカウントとタイマーを更新
                click_count += 1
                last_click_time = current_time

            # ボタンの状態をリセット
            button_pressed = False
    
    # 連続クリック判定タイマー
    if select_mode and not is_playing and click_count > 0 and time.ticks_diff(time.ticks_ms(), last_click_time) > 500:
        if click_count == 1:
            print("短押し1回（次に進む）")
            selected_scenario += 1
            # 数字キーのみを対象とするため、keys()から数字キーだけを取得して最大値をチェック
            scenario_nums = [k for k in scenarios_data.keys() if isinstance(k, int)]
            if scenario_nums and selected_scenario > max(scenario_nums):
                selected_scenario = min(scenario_nums)
        elif click_count == 2:
            print("短押し2回（前に戻る）")
            selected_scenario -= 1
            scenario_nums = [k for k in scenarios_data.keys() if isinstance(k, int)]
            if scenario_nums and selected_scenario < min(scenario_nums):
                selected_scenario = max(scenario_nums)

        # 共通の表示更新
        new_display = f"Select: {selected_scenario}"
        if new_display != current_display:
            # --- 修正箇所: show_display を push_message に変更 ---
            oled_patterns.push_message([new_display])
            # ----------------------------------------------------
            current_display = new_display

        # カウントとタイマーをリセット
        click_count = 0
        last_click_time = 0
        last_press_time = time.ticks_ms()

    # 通常モードの処理
    elif not select_mode:
        # ボタンが押されたときのみ処理
        if button.value() == 1 and not is_playing:
            print("通常モード：抽選開始")
            is_playing = True
            
            # 抽選と再生をスレッドで開始
            selected_num, command_list = effects.playRandomEffect(scenarios_data) 
            
            if command_list:
                _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, selected_num, stop_flag, play_complete_callback))

                # 再生開始時の表示
                new_display = f"Now playing: {selected_num}"
                if new_display != current_display:
                    # --- 修正箇所: show_display を push_message に変更 ---
                    oled_patterns.push_message([new_display])
                    # ----------------------------------------------------
                    current_display = new_display
            else:
                is_playing = False
                new_display = "No scenarios found"
                if new_display != current_display:
                    # --- 修正箇所: show_display を push_message に変更 ---
                    oled_patterns.push_message([new_display])
                    # ----------------------------------------------------
                    current_display = new_display
            
            # ボタンが離れるのを待つ
            while button.value() == 1:
                time.sleep(0.1)

        # 再生中でない場合のみ "Push the button" を表示
        if not is_playing:
            new_display = push_message
            if new_display != current_display:
                # --- 修正箇所: show_display を push_message に変更 ---
                oled_patterns.push_message([new_display])
                # ----------------------------------------------------
                current_display = new_display
                
    time.sleep_ms(10)
