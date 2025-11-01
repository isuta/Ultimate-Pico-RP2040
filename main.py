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
import onboard_led
import volume_control
import hardware_init
import display_manager

# 入力用のプルダウン抵抗を使用するピンとして設定。
try:
    button = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
    button_available = True
    print(f"Button initialized on pin {config.BUTTON_PIN}")
except Exception as e:
    print(f"Warning: Button initialization failed on pin {config.BUTTON_PIN}: {e}")
    print("Button functionality will be disabled. Program will run in console-only mode.")
    button = None
    button_available = False

# --- Potentiometer/ADC Initialization ---
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

# configからタイミング設定値を読み込み (存在しない場合はデフォルト値を適用)
# ----------------------------------------------------------------------
IDLE_TIMEOUT_MS = getattr(config, 'IDLE_TIMEOUT_MS', 300000) # 300000ms = 5分
POLLING_DELAY_MS = getattr(config, 'MAIN_LOOP_POLLING_MS', 10) # メインループの待機時間 (ms)

# 自動再生間隔はconfigに定義されていないため、デフォルト値をミリ秒に変換して使用
# (IDLE_TIMEOUTを超えてから、この間隔で再生を繰り返す)
AUTO_PLAY_INTERVAL_MS = getattr(config, 'AUTO_PLAY_INTERVAL_SECONDS', 60) * 1000
# ----------------------------------------------------------------------


# JSONファイルを読み込む関数
def load_scenarios(filename):
    """
    指定されたJSONファイルからシナリオデータを読み込み、
    セレクトモード用(すべて)とランダムモード用(数字形式のみ)にキーを分類して返します。
    """
    with open(filename, 'r') as f:
        scenarios = json.load(f)

    selectable_keys = []  # セレクトモード用 (すべての有効なキー)
    random_keys = []      # ランダムモード用 (数字または_付き数字のみ)
    filtered_scenarios = {} # 最終的な辞書

    for k, v in scenarios.items():
        # キーは文字列であり、空ではないことを確認
        if not isinstance(k, str) or not k:
            continue

        # --- ランダム抽選対象の判定ロジック ---
        # キーが数字のみ (例: "1") または
        # アンダースコアから始まり、その後に数字のみが続く (例: "_101", "__5")
        is_digit_like = k.isdigit() or (k.lstrip('_').isdigit() and k.startswith('_'))

        # すべての有効なキーをセレクトモードの対象として追加
        filtered_scenarios[k] = v
        selectable_keys.append(k)

        # ランダム抽選の対象は、数字形式のキーのみ
        if is_digit_like:
            random_keys.append(k)

    # セレクトモード用のキーリストはソートする
    return filtered_scenarios, sorted(selectable_keys), random_keys

# 初期化
button_pressed = False
press_time = 0
release_time = 0

# シナリオの選択状態
selected_index = 0
selected_scenario = "1" 
last_press_time = 0  # 最後にボタンが押された時間を記録
select_mode = False  # セレクトモード判定
current_display = "" # 現在表示されている文字列を保持（セレクトモード時は選択中のキーを保持）
push_message = "Push the button" # ボタンを押してもらうために表示する文字列
select_mode_message = "Select Mode" # セレクトモードのときに表示する文字列
click_count = 0  # 連続短押しカウント
last_click_time = 0 # 前回の短押しが離された時間

# --- アイドル検出のための時間トラッキング ---
last_user_interaction_time = time.ticks_ms() # 最後にユーザーがボタンまたはボリュームを操作した時間
last_auto_play_time = time.ticks_ms()       # 最後に自動再生を実行した時間
# ----------------------------------------------------

# シナリオのリスト
valid_scenarios = []  
random_scenarios = [] 

# 停止フラグの定義（リストにすることで参照渡しを実現）
stop_flag = [False]
# シナリオ実行中かどうかのフラグ
is_playing = False

# シナリオデータを読み込み
try:
    # 戻り値を3つ受け取る
    scenarios_data, valid_scenarios, random_scenarios = load_scenarios('scenarios.json')

    if not scenarios_data:
        raise Exception("scenarios.json is empty or invalid.")

    # 最初の有効なキーを初期選択値とする
    if valid_scenarios:
        selected_scenario = valid_scenarios[selected_index]
    else:
        raise Exception("No valid scenarios found.")

except Exception as e:
    print(f"Error loading scenarios: {e}")
    print("Creating minimal fallback scenario for console mode...")
    
    # フォールバック用の最小限のシナリオを作成
    scenarios_data = {
        "1": [
            ["delay", 1000],
            {"type": "led", "command": "fill", "strip": "all", "color": [255, 0, 0], "duration": 2000},
            ["delay", 1000],
            {"type": "led", "command": "off"}
        ],
        "2": [
            ["sound", 1, 1],
            ["delay", 3000]
        ]
    }
    
    select_mode_message = "Fallback Mode"
    valid_scenarios = ["1", "2"]
    random_scenarios = ["1", "2"]
    selected_scenario = "1" # フォールバック時は1とする
    print("Fallback scenarios created. System will continue with basic functionality.")

# ハードウェア初期化を hardware_init に移譲
hw = hardware_init.init_hardware(config, oled_patterns, led_patterns, onboard_led, sound_patterns)

# 返却されたリソースを展開
button = hw.get('button')
button_available = hw.get('button_available', False)
volume_pot = hw.get('volume_pot')
init_messages = hw.get('init_messages', [])
final_messages = hw.get('final_messages', [])
# Display manager
dm = display_manager.DisplayManager(oled_patterns)

# --- 初期ボリューム設定とADC読み取りの確認 ---
# volume_control にロジックを移譲
vc = volume_control.PollingVolumeController(volume_pot, sound_patterns, oled_patterns, config)
initial_volume = vc.init_initial_volume()

if volume_pot and initial_volume is not None and sound_patterns.is_dfplayer_available():
    current_volume = initial_volume
    LAST_VOLUME_READING = vc.last_adc or 0
    print(f"Initial Volume set to {current_volume} (ADC: {LAST_VOLUME_READING})")
    final_messages = [f'Vol:{current_volume}', 'Init End']

elif volume_pot and initial_volume is not None and not sound_patterns.is_dfplayer_available():
    # ADCは利用可能だがDFPlayerが利用不可の場合
    current_volume = initial_volume
    LAST_VOLUME_READING = vc.last_adc or 0
    print(f"Volume potentiometer detected (ADC: {LAST_VOLUME_READING}), but DFPlayer unavailable.")
    final_messages = [f'Vol:{current_volume}', 'No Audio', 'Init End']

elif not volume_pot and sound_patterns.is_dfplayer_available():
    # DFPlayerは利用可能だがADCが利用不可の場合
    print("DFPlayer available, but volume potentiometer skipped due to initialization error.")
    final_messages = ['Audio: OK', 'No Volume Ctrl', 'Init End']

else:
    # 両方とも利用不可の場合
    print("Both volume potentiometer and DFPlayer skipped due to initialization errors.")

# ボタンが利用できない場合のメッセージを追加
if not button_available:
    final_messages = ['Console Mode'] + final_messages
    
dm.push_message(final_messages) # 初期化完了表示

# 利用可能な機能をコンソールにサマリ表示
print("\n=== System Ready ===")
print(f"Button: {'Available' if button_available else 'Console Mode'}")
print(f"OLED: {'Available' if oled_patterns.is_oled_available() else 'Console Output'}")
print(f"Audio: {'Available' if sound_patterns.is_dfplayer_available() else 'Disabled'}")
print(f"LED: {'Available' if led_patterns.is_neopixel_available() else 'Disabled'}")
print(f"Onboard LED: {'Available' if onboard_led.is_onboard_led_available() else 'Disabled'}")
if volume_pot and sound_patterns.is_dfplayer_available():
    print(f"Volume Control: Available")
else:
    print(f"Volume Control: Disabled")
print("===================")

# システム起動完了を内蔵LEDで示す
if onboard_led.is_onboard_led_available():
    print("System startup complete. Onboard LED indicating ready state...")
    onboard_led.blink(times=2, on_time_ms=300, off_time_ms=200)

time.sleep(1)
# ----------------------------------------------------

# 長押しによるセレクトモードへの移行チェック
if button_available and button.value() == 1:
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
elif not button_available:
    # ボタンが利用できない場合、通常モードでアイドル自動再生として動作
    print("Console-only mode: No button detected.")
    print("Running in normal mode with automatic idle playback.")
    select_mode = False  # 通常モードに設定
    # アイドルタイムアウトを即座に開始するため、初期時間を調整
    last_user_interaction_time = time.ticks_ms() - IDLE_TIMEOUT_MS

# --- セレクトモード表示ヘルパー関数 ---
def update_oled_select_mode_display():
    """
    セレクトモード時のOLED表示を「Select Mode」と「シナリオキー」の2行で更新し、
    current_displayを新しいシナリオキーに設定します。
    """
    global current_display, selected_scenario, select_mode_message

    # 1行目にモード名、2行目に選択中のキーを表示
    dm.push_message([select_mode_message, selected_scenario])
    # current_displayは選択キー自体を保持するようにする
    current_display = selected_scenario
# ----------------------------------------------


# 最初の表示を一度だけ行う
if select_mode:
    # 共通関数を呼び出し、2行表示にする
    update_oled_select_mode_display()
else:
    current_display = push_message
    dm.push_message([current_display])


# シナリオ再生をスレッドで実行するためのラッパー関数
def play_scenario_in_thread(data, num, flag, callback):
    """
    シナリオをスレッド内で実行し、完了後にコールバックを呼び出す。
    numはシナリオキー（文字列）。
    """
    # シナリオ実行開始時に内蔵LEDを点灯
    onboard_led.turn_on()
    print(f"Onboard LED: ON (Scenario {num} started)")
    
    effects.playEffectByNum(data, num, flag)
    callback()

def play_complete_callback():
    """
    シナリオ再生完了時に実行されるコールバック関数。
    """
    # 【修正1】global宣言を関数の先頭に移動
    global is_playing, current_display, push_message
    
    # シナリオ実行完了時に内蔵LEDを消灯
    onboard_led.turn_off()
    print("Onboard LED: OFF (Scenario completed)")
    
    is_playing = False
    stop_flag[0] = False # 停止フラグをリセット
    print("再生スレッドが終了しました。")

    # 再生完了後、セレクトモードの場合は選択画面表示に戻す
    if select_mode:
        update_oled_select_mode_display()
    # 通常モードの場合も、待機メッセージに戻す（アイドルチェックに任せるため不要だが念のため）
    else:
        # 通常モードの待機メッセージに戻す
        if current_display != push_message:
            dm.push_message([push_message])
            current_display = push_message


# ボタン入力待ちループ
loop_counter = 0
adc_check_interval = int(100 / POLLING_DELAY_MS) # 100msごとにADCをチェックするためのカウンタ値 (例: 100ms / 10ms = 10)
if adc_check_interval < 1:
    adc_check_interval = 1 # 少なくとも毎ループチェック

    # コンソール専用モードの場合、動作説明を表示
if not button_available:
    print("\n=== Console-Only Mode ===")
    print("Running in console-only mode due to button initialization failure.")
    print("System will automatically start random playback after idle timeout.")
    print(f"Idle timeout: {IDLE_TIMEOUT_MS/1000} seconds")
    print(f"Auto-play interval: {AUTO_PLAY_INTERVAL_MS/1000} seconds")
    if onboard_led.is_onboard_led_available():
        print("Onboard LED will indicate scenario execution status:")
        print("  - LED ON: Scenario executing")
        print("  - LED OFF: Scenario completed / idle")
    print("Monitor console output for system status and scenario execution.")
    print("=========================\n")

while True:
    current_time = time.ticks_ms()

    # --- ボリューム調整ロジック ---
    # volume_control.PollingVolumeController に処理を委譲
    if 'vc' in globals():
        res = vc.poll(current_time)
        # アイデル判定（最後のユーザー操作からの経過が閾値以上か）
        is_idle = time.ticks_diff(current_time, last_user_interaction_time) >= IDLE_TIMEOUT_MS

        # ボリューム変化があった場合の処理
        if res.get('changed'):
            current_volume = res.get('volume')
            # アイドル状態ではコンソール出力／OLED更新を抑制する
            if not is_idle:
                print(f"Volume updated to {current_volume} (ADC: {vc.last_adc})")
                # OLEDは main 側で current_display を知っているのでここで表示更新
                dm.push_message([f'Vol: {current_volume}', current_display])

            # ユーザー操作のタイムスタンプは、アイドルでなければ更新する
            # （アイドル中のノイズで頻繁に復帰しないようにするため）
            if res.get('updated_last_user') and not is_idle:
                last_user_interaction_time = current_time
    # ------------------------------------

    # --- 既存のボタン処理ロジック (select_mode/normal mode) ---
    if select_mode and valid_scenarios and button_available: 
        current_button_value = button.value()
        num_valid_scenarios = len(valid_scenarios)

        # デバウンス処理
        if time.ticks_diff(current_time, last_press_time) < 300:
            time.sleep_ms(10)
            continue
        
        # ボタンが押されている場合
        if current_button_value == 1:
            if not button_pressed:
                button_pressed = True
                press_time = current_time
                # 【追加】ボタンが押されたときもユーザー操作時間を更新
                last_user_interaction_time = current_time

            # 長押し（実行開始）
            if not is_playing and time.ticks_diff(current_time, press_time) >= 1000:
                print(f"長押し（実行開始）: Scenario {selected_scenario}")
                is_playing = True
                
                # selected_scenario は文字列として渡される
                _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, selected_scenario, stop_flag, play_complete_callback))

                new_display = f"Executing: {selected_scenario}"
                # 実行中は1行表示に切り替え
                if new_display != current_display:
                    dm.push_message([new_display])
                    current_display = new_display
                
                # ボタンが離されるのを待つ
                while button.value() == 1:
                    time.sleep(0.1)
                button_pressed = False
                last_press_time = time.ticks_ms()

                # ユーザー操作時間を更新
                last_user_interaction_time = time.ticks_ms()

                # 実行開始後は元のセレクトメッセージに戻す
                update_oled_select_mode_display()


        # ボタンが離された場合
        elif button_pressed and current_button_value == 0:
            press_duration = time.ticks_diff(current_time, press_time)

            # 再生中に短押しを検知した場合 (強制停止)
            if is_playing and press_duration < 500:
                print("短押しによる停止を検知")
                stop_flag[0] = True # スレッド内で停止処理が行われる
                
                # 強制停止時に内蔵LEDを即座に消灯
                onboard_led.turn_off()
                print("Onboard LED: OFF (Force stopped)")

                # ユーザー操作時間を更新
                last_user_interaction_time = time.ticks_ms()

                # 停止後、選択画面表示に戻す
                update_oled_select_mode_display()

            # 再生中でない場合の短押し（選択動作）
            elif not is_playing and press_duration < 500:
                click_count += 1
                last_click_time = current_time

                # ユーザー操作時間を更新
                last_user_interaction_time = time.ticks_ms()

            button_pressed = False

        # 連続クリック判定タイマー
        if not is_playing and click_count > 0 and time.ticks_diff(time.ticks_ms(), last_click_time) > 500:

            # selected_indexを操作し、selected_scenarioをリストから取得する
            if click_count == 1:
                print("短押し1回（次に進む）")
                # リストの最後に到達したら0に戻る
                selected_index = (selected_index + 1) % num_valid_scenarios
            elif click_count == 2:
                print("短押し2回（前に戻る）")
                # 0より小さくなったらリストの最後に移動
                selected_index = (selected_index - 1 + num_valid_scenarios) % num_valid_scenarios # 負の数に対応
            else:
                # 3回以上クリックの場合は無視し、次のシナリオに進む
                selected_index = (selected_index + 1) % num_valid_scenarios
                print(f"短押し{click_count}回を検知（次に進む）")

            # 選択されたシナリオ番号を更新 (valid_scenariosの要素は文字列)
            selected_scenario = valid_scenarios[selected_index]

            # 共通関数を呼び出し、2行表示を更新
            update_oled_select_mode_display()

            click_count = 0
            last_click_time = 0
            last_press_time = time.ticks_ms()

    # 通常モードの処理
    elif not select_mode and button_available:
        # ボタンが押されたときのみ処理
        if button.value() == 1:
            print("通常モード：抽選開始（手動）")

            # ユーザー操作時間を更新
            last_user_interaction_time = current_time 
            # 自動再生タイマーをリセット
            last_auto_play_time = current_time

            if not is_playing:
                is_playing = True
                # 抽選と再生をスレッドで開始 (手動再生は既存ロジック)
                if not random_scenarios:
                    num = "-1" # 抽選対象がない
                    command_list = []
                else:
                    try:
                        # effects.playRandomEffect(scenarios_data) があれば実行 
                        num, command_list = effects.playRandomEffect(scenarios_data) 
                    except AttributeError:
                        # effects.py に playRandomEffect がない場合の代替処理
                        if random_scenarios: 
                            print("Warning: effects.playRandomEffect not found. Using random choice from filtered keys.")
                            num = random.choice(random_scenarios)
                            command_list = scenarios_data.get(num, [])
                        else:
                            num = "-1" 
                            command_list = []

                if command_list:
                    # num は文字列として渡される
                    _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, num, stop_flag, play_complete_callback))

                    # 再生開始時の表示
                    new_display = f"Now playing: {num}"
                    if new_display != current_display:
                        dm.push_message([new_display])
                        current_display = new_display
                else:
                    is_playing = False
                    new_display = "No scenarios found"
                    if new_display != current_display:
                        dm.push_message([new_display])
                        current_display = new_display

            # ボタンが離れるのを待つ
            while button.value() == 1:
                time.sleep(0.1)

        # 再生中でない場合のみ "Push the button" を表示
        if not is_playing:
            new_display = push_message
            if new_display != current_display:
                dm.push_message([new_display])
                current_display = new_display

    # ----------------------------------------------------------------------
    # --- アイドル状態の自動再生チェック (通常モードのみ) ---
    # ----------------------------------------------------------------------

    if not select_mode and not is_playing and random_scenarios:
        
        # 最後にユーザーが操作してからどれくらい経過したか
        time_since_last_action = time.ticks_diff(current_time, last_user_interaction_time)
        
        # 1. アイドルタイムアウトを超えているか？ (例: 5分)
        if time_since_last_action >= IDLE_TIMEOUT_MS:

            # 2. 自動再生間隔を超えているか？ (例: 1分)
            time_since_last_auto_play = time.ticks_diff(current_time, last_auto_play_time)

            if time_since_last_auto_play >= AUTO_PLAY_INTERVAL_MS:

                if button_available:
                    print("アイドルタイムアウト。自動ランダム再生を開始します。")
                else:
                    print(f"Console Mode: Auto-play scenario (interval: {AUTO_PLAY_INTERVAL_MS/1000}s)")
                    
                is_playing = True

                # 抽選と再生ロジック
                try:
                    num, command_list = effects.playRandomEffect(scenarios_data) 
                except AttributeError:
                    # effects.py に playRandomEffect がない場合の代替処理
                    num = random.choice(random_scenarios)
                    command_list = scenarios_data.get(num, [])

                if command_list:
                    # num は文字列として渡される
                    _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, num, stop_flag, play_complete_callback))

                    # 再生開始時の表示
                    new_display = f"Auto Play: {num}"
                    if new_display != current_display:
                        dm.push_message([new_display])
                        current_display = new_display
                else:
                    is_playing = False
                    print("Warning: Auto Play failed, no command list.")

                # 自動再生時間を更新
                last_auto_play_time = current_time 

    # 【修正】ループの最後でconfigで定義されたポーリング遅延時間だけ待機
    time.sleep_ms(POLLING_DELAY_MS)
    loop_counter += 1
