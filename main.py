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

        # --- 【修正】ランダム抽選対象の判定ロジックを厳密化 ---
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

# 【修正】シナリオ番号ではなく、リストのインデックスを使用
selected_index = 0
# 実際に選択されているシナリオキー（表示用/実行用） - キーは常に文字列
selected_scenario = "1" 
last_press_time = 0  # 最後にボタンが押された時間を記録
select_mode = False  # セレクトモード判定
current_display = "" # 現在表示されている文字列を保持（セレクトモード時は選択中のキーを保持）
push_message = "Push the button" # ボタンを押してもらうために表示する文字列
select_mode_message = "Select Mode" # セレクトモードのときに表示する文字列
click_count = 0  # 連続短押しカウント
last_click_time = 0 # 前回の短押しが離された時間

# 【更新】
valid_scenarios = [] # 実際に存在するシナリオキーのリスト（文字列、セレクトモード用）
random_scenarios = [] # 【追加】ランダム再生用のシナリオキーのリスト（数字/アンダースコア付き数字のみ）

# 停止フラグの定義（リストにすることで参照渡しを実現）
stop_flag = [False]
# シナリオ実行中かどうかのフラグ
is_playing = False

# シナリオデータを読み込み
try:
    # 戻り値を3つ受け取るように変更
    scenarios_data, valid_scenarios, random_scenarios = load_scenarios('scenarios.json')
    
    if not scenarios_data:
        raise Exception("scenarios.json is empty or invalid.")
    
    # セレクトモード用のキーが存在するか確認
    if valid_scenarios:
        # 最初の有効なキーを初期選択値とする
        selected_scenario = valid_scenarios[selected_index]
    else:
        raise Exception("No valid scenarios found.")
        
except Exception as e:
    print(f"Error loading scenarios: {e}")
    scenarios_data = {}
    select_mode_message = "File Error"
    valid_scenarios = []
    random_scenarios = []
    selected_scenario = "0" # ファイルエラー時は0とする

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

# --- NEW: セレクトモード表示ヘルパー関数 ---
def update_oled_select_mode_display():
    """
    セレクトモード時のOLED表示を「Select Mode」と「シナリオキー」の2行で更新し、
    current_displayを新しいシナリオキーに設定します。
    """
    global current_display, selected_scenario, select_mode_message
    
    # 1行目にモード名、2行目に選択中のキーを表示
    oled_patterns.push_message([select_mode_message, selected_scenario])
    # current_displayは選択キー自体を保持するようにする
    current_display = selected_scenario
# ----------------------------------------------


# 最初の表示を一度だけ行う
if select_mode:
    # 【修正】共通関数を呼び出し、2行表示にする
    update_oled_select_mode_display()
else:
    current_display = push_message
    oled_patterns.push_message([current_display])
# 【削除】元のコードにあった oled_patterns.push_message([current_display]) は不要


# シナリオ再生をスレッドで実行するためのラッパー関数
def play_scenario_in_thread(data, num, flag, callback):
    """
    シナリオをスレッド内で実行し、完了後にコールバックを呼び出す。
    numはシナリオキー（文字列）。
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
    
    # 【追加】再生完了後、セレクトモードの場合は選択画面表示に戻す
    if select_mode:
        update_oled_select_mode_display()


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
                # current_displayはセレクトモード時は選択キー、通常モード時はpush_message/Now playing
                oled_patterns.push_message([f'Vol: {current_volume}', current_display])
            
        LAST_VOLUME_READING = adc_value
    # ------------------------------------

    # --- 既存のボタン処理ロジック (select_mode/normal mode) ---
    if select_mode and valid_scenarios: # 【追加】有効なシナリオが存在する場合のみ実行
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

            # 長押し（実行開始）
            if not is_playing and time.ticks_diff(current_time, press_time) >= 1000:
                print(f"長押し（実行開始）: Scenario {selected_scenario}")
                is_playing = True
                
                # selected_scenario は文字列として渡される
                _thread.start_new_thread(play_scenario_in_thread, (scenarios_data, selected_scenario, stop_flag, play_complete_callback))

                new_display = f"Executing: {selected_scenario}"
                # 実行中は1行表示に切り替え
                if new_display != current_display:
                    oled_patterns.push_message([new_display])
                    current_display = new_display
                
                # ボタンが離されるのを待つ
                while button.value() == 1:
                    time.sleep(0.1)
                button_pressed = False
                last_press_time = time.ticks_ms()
                
                # 実行開始後は元のセレクトメッセージに戻す
                # 【修正】共通関数を呼び出し、2行表示に戻す
                update_oled_select_mode_display()


        # ボタンが離された場合
        elif button_pressed and current_button_value == 0:
            press_duration = time.ticks_diff(current_time, press_time)
            
            # 再生中に短押しを検知した場合 (強制停止)
            if is_playing and press_duration < 500:
                print("短押しによる停止を検知")
                stop_flag[0] = True # スレッド内で停止処理が行われる
                button_pressed = False
                last_press_time = time.ticks_ms()
                
                # 停止後、選択画面表示に戻す
                # 【修正】共通関数を呼び出し、2行表示に戻す
                update_oled_select_mode_display()

            # 再生中でない場合の短押し（選択動作）
            elif not is_playing and press_duration < 500:
                click_count += 1
                last_click_time = current_time

            button_pressed = False
        
        # 連続クリック判定タイマー
        if not is_playing and click_count > 0 and time.ticks_diff(time.ticks_ms(), last_click_time) > 500:
            
            # 【修正】selected_indexを操作し、selected_scenarioをリストから取得する
            if click_count == 1:
                print("短押し1回（次に進む）")
                # リストの最後に到達したら0に戻る
                selected_index = (selected_index + 1) % num_valid_scenarios
            elif click_count == 2:
                print("短押し2回（前に戻る）")
                # 0より小さくなったらリストの最後に移動
                selected_index = (selected_index - 1) % num_valid_scenarios

            # 選択されたシナリオ番号を更新 (valid_scenariosの要素は文字列)
            selected_scenario = valid_scenarios[selected_index]
            
            # 【修正】共通関数を呼び出し、2行表示を更新
            update_oled_select_mode_display()

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
            if not random_scenarios:
                num = "-1" # 抽選対象がない
                command_list = []
            else:
                try:
                    # effects.playRandomEffect(scenarios_data) があれば実行 (ランダムキーの選択はeffects.pyに任せる)
                    num, command_list = effects.playRandomEffect(scenarios_data) 
                except AttributeError:
                    # effects.py に playRandomEffect がない場合の代替処理（テスト用）
                    if random_scenarios: 
                        print("Warning: effects.playRandomEffect not found. Using random choice from filtered keys.")
                        # random_scenarios は数字または_付き数字のキーのみを含む
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
