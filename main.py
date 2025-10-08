# main.py
import config
from machine import Pin, ADC # ADCをインポート
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

# --- NEW: Potentiometer/ADC Initialization ---
# ポテンショメータのピン設定
try:
    volume_pot = ADC(Pin(config.POTENTIOMETER_PIN))
except ValueError as e:
    print(f"Error initializing ADC on pin {config.POTENTIOMETER_PIN}: {e}")
    # 失敗した場合は None を設定してメインループでスキップ
    volume_pot = None

# ボリュームトラッキング用の変数
current_volume = -1 # 初期値 -1 で強制的に初回更新
LAST_VOLUME_READING = 0 # 最後に読み取ったADC値を保持

# 初期待ち
time.sleep(2.0)

# JSONファイルを読み込む関数
def load_scenarios(filename):
    """
    指定されたJSONファイルからシナリオデータを読み込みます。
    キー（文字列）を整数に変換します。
    """
    with open(filename, 'r') as f:
        scenarios = json.load(f)
    # キーを文字列から整数に変換
    return {int(k): v for k, v in scenarios.items()}

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
max_scenario = 0 # シナリオの最大番号

# 停止フラグの定義（リストにすることで参照渡しを実現）
stop_flag = [False]
# シナリオ実行中かどうかのフラグ
is_playing = False

# シナリオデータを読み込み
try:
    scenarios_data = load_scenarios('scenarios.json')
    if not scenarios_data:
        raise Exception("scenarios.json is empty or invalid.")
    max_scenario = max(scenarios_data.keys())
except Exception as e:
    print(f"Error loading scenarios: {e}")
    scenarios_data = {}
    select_mode_message = "File Error"
    max_scenario = 0 # ファイルエラー時は最大シナリオを0とする

# 初期化と起動表示
oled_patterns.init_oled()

oled_patterns.push_message(['Loading...']) # ロード中表示
led_patterns.init_neopixels()  # NeoPixelの初期化
sound_patterns.init_dfplayer()
time.sleep(1) # DFPlayer初期化待ち

# --- NEW: 初期ボリューム設定とADC読み取りの確認 ---
if volume_pot:
    # ADC値(0-65535)をボリューム(0-30)にマッピング
    initial_adc_value = volume_pot.read_u16()
    initial_volume = int(initial_adc_value * config.DFPLAYER_MAX_VOLUME / 65535)
    
    # 初期ボリュームをDFPlayerに設定
    sound_patterns.set_volume(initial_volume)
    current_volume = initial_volume
    LAST_VOLUME_READING = initial_adc_value
    print(f"Initial Volume set to {current_volume} (ADC: {initial_adc_value})")
    oled_patterns.push_message([f'Vol:{current_volume}', 'Init End']) # 初期化完了表示
else:
    print("Volume Potentiometer skipped due to initialization error.")
    oled_patterns.push_message(['Init End']) # 初期化完了表示

time.sleep(1)
# ----------------------------------------------------

# 長押しによるセレクトモードへの移行チェック
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

oled_patterns.push_message([current_display])

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
    stop_flag[0] = False # 停止フラグをリセット
    print("再生スレッドが終了しました。")

# ボタン入力待ちループ
while True:
    current_time = time.ticks_ms()

    # --- NEW: ボリューム調整ロジック ---
    if volume_pot and current_time % 100 < 10: # 100msごとにチェック (ループ負荷軽減のため)
        adc_value = volume_pot.read_u16()
        
        # デッドゾーンチェック: 前回の値から大きく変わっていなければ無視
        if abs(adc_value - LAST_VOLUME_READING) > config.VOLUME_DEADZONE:
            # ADC値(0-65535)をボリューム(0-30)にマッピング
            new_volume = int(adc_value * config.DFPLAYER_MAX_VOLUME / 65535)
            # ボリュームが最大値を超えないようにクリップ
            new_volume = max(0, min(new_volume, config.DFPLAYER_MAX_VOLUME))
            
            # ボリュームが変わった場合のみ更新
            if new_volume != current_volume:
                sound_patterns.set_volume(new_volume)
                current_volume = new_volume
                LAST_VOLUME_READING = adc_value
                print(f"Volume updated to {current_volume} (ADC: {adc_value})")
                
                # ボリューム変更をOLEDに一時表示
                # 常に1行目にボリューム、2行目に現在のモード/メッセージを表示
                oled_patterns.push_message([f'Vol: {current_volume}', current_display])
            
        LAST_VOLUME_READING = adc_value
    # ------------------------------------

    # --- 既存のボタン処理ロジック (select_mode/normal mode) ---
    if select_mode:
        current_button_value = button.value()

        # デバウンス処理
        if time.ticks_diff(current_time, last_press_time) < 300:
            time.sleep_ms(10)
            continue
        
        # ボタンが押されている場合
        if current_button_value == 1:
            if not button_pressed:
                button_pressed = True
                press_time = current_time

            if not is_playing and time.ticks_diff(current_time, press_time) >= 1000:
                print("長押し（実行開始）")
                is_playing = True
                
                _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, selected_scenario, stop_flag, play_complete_callback))

                new_display = f"Executing: {selected_scenario}"
                if new_display != current_display:
                    oled_patterns.push_message([new_display])
                    current_display = new_display
                
                while button.value() == 1:
                    time.sleep(0.1)
                button_pressed = False
                last_press_time = time.ticks_ms()
                
                new_display = select_mode_message
                if new_display != current_display:
                    oled_patterns.push_message([new_display])
                    current_display = new_display

        # ボタンが離された場合
        elif button_pressed and current_button_value == 0:
            press_duration = time.ticks_diff(current_time, press_time)
            
            # 再生中に短押しを検知した場合 (強制停止)
            if is_playing and press_duration < 500:
                print("短押しによる停止を検知")
                stop_flag[0] = True
                button_pressed = False
                last_press_time = time.ticks_ms()
                new_display = select_mode_message
                if new_display != current_display:
                    oled_patterns.push_message([new_display])
                    current_display = new_display

            # 再生中でない場合の短押し（選択動作）
            elif not is_playing and press_duration < 500:
                click_count += 1
                last_click_time = current_time

            button_pressed = False
    
        # 連続クリック判定タイマー
        if not is_playing and click_count > 0 and time.ticks_diff(time.ticks_ms(), last_click_time) > 500:
            if click_count == 1:
                print("短押し1回（次に進む）")
                selected_scenario += 1
                if selected_scenario > max_scenario:
                    selected_scenario = 1
            elif click_count == 2:
                print("短押し2回（前に戻る）")
                selected_scenario -= 1
                if selected_scenario < 1:
                    selected_scenario = max_scenario

            new_display = f"Select: {selected_scenario}"
            if new_display != current_display:
                oled_patterns.push_message([new_display])
                current_display = new_display

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
            try:
                # effects.playRandomEffect(scenarios_data) があれば実行
                num, command_list = effects.playRandomEffect(scenarios_data) 
            except AttributeError:
                # effects.py に playRandomEffect がない場合の代替処理（テスト用）
                if max_scenario > 0:
                    print("Warning: effects.playRandomEffect not found. Using random choice.")
                    num = random.choice(list(scenarios_data.keys()))
                    command_list = scenarios_data.get(num, [])
                else:
                    num = -1
                    command_list = []
            
            if command_list:
                _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, num, stop_flag, play_complete_callback))

                # 再生開始時の表示
                new_display = f"Now playing: {num}"
                if new_display != current_display:
                    oled_patterns.push_message([new_display])
                    current_display = new_display
            else:
                is_playing = False
                new_display = "No scenarios found"
                if new_display != current_display:
                    oled_patterns.push_message([new_display])
                    current_display = new_display
            
            # ボタンが離れるのを待つ
            while button.value() == 1:
                time.sleep(0.1)

        # 再生中でない場合のみ "Push the button" を表示
        if not is_playing:
            new_display = push_message
            if new_display != current_display:
                oled_patterns.push_message([new_display])
                current_display = new_display
    
    # ループの最後で少し待機
    time.sleep_ms(10)
