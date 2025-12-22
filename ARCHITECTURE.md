# システムアーキテクチャ

このドキュメントでは、Ultimate-Pico-RP2040プロジェクトの内部構造とデータフローを説明します。

---

## 📐 システム全体構造

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                    (エントリーポイント)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    system_init.py                            │
│            (システム初期化・モジュール読み込み)                 │
└────────┬────────────┬────────────┬────────────┬─────────────┘
         │            │            │            │
         ↓            ↓            ↓            ↓
  hardware_init  config.py  scenarios.json  各種モジュール初期化
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│                   loop_controller.py                         │
│                  (メインループ制御)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              state_manager.py (132行) ⭐ REFACTORED          │
│                  【状態統合調整役】                           │
│            (3クラスを統合、軽量化)                            │
├────────────┬────────────┬────────────────────────────────────┤
│ button_    │ playback_  │ autoplay_                          │
│ handler.py │ manager.py │ controller.py                      │
│ (102行)    │ (120行)    │ (67行)                             │
│ ⭐ NEW     │ ⭐ NEW     │ ⭐ NEW                             │
└────────────┴────────────┴────────────────────────────────────┘
             │            │            │
             ↓            ↓            ↓
      ボタン入力    シナリオ再生   自動再生制御
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 effects.py (145行) ⭐ REFACTORED             │
│            【コマンドディスパッチャー】                         │
│         (コマンドタイプ判定→ハンドラーへ振り分け)               │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│           command_parser.py ⭐ NEW (共通ユーティリティ)        │
│    (JSON解析・バリデーション・stop_flag監視・エラー処理)        │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│         コマンドハンドラー層 ⭐ NEW (中間層)                   │
│  ┌──────────────┬─────────────┬──────────────────┐          │
│  │ servo_cmd    │ led_cmd     │ pwm_led_cmd      │          │
│  │ _handler.py  │ _handler.py │ _handler.py      │          │
│  ├──────────────┼─────────────┼──────────────────┤          │
│  │ motor_cmd    │ sound_cmd   │                  │          │
│  │ _handler.py  │ _handler.py │                  │          │
│  └──────────────┴─────────────┴──────────────────┘          │
│        (各100-150行、デバイス固有処理のみ)                     │
└──┬──────┬──────┬──────┬──────┬──────────────────────────────┘
   │      │      │      │      │
   ↓      ↓      ↓      ↓      ↓
servo   neopixel pwm_led motor sound
rotation/ _ctrl   _ctrl   (stepper) _patterns
position
_ctrl
```

---

## 🧩 モジュール呼び出しの設計方針

このシステムでは、モジュールの呼び出し方法を以下のように使い分けています：

### 外部機器制御モジュール → effects.py経由（3層アーキテクチャ）⭐ REFACTORED
**NeoPixel、PWM LED、DFPlayer Mini、ステッピングモーター、サーボモーター** など、外部デバイスや拡張デバイスを制御するモジュールは、**effects.py → コマンドハンドラー → 各モジュール** の3層構造で呼び出されます。

**アーキテクチャ（2025-12-22にリファクタ）:**
```
effects.py (145行)
  ↓ コマンドタイプ判定のみ
command_parser.py (共通ユーティリティ)
  ↓ JSON解析・バリデーション
コマンドハンドラー層 (各100-150行)
  ↓ デバイス固有処理
各モジュール (変更なし)
```

**理由:**
- JSONシナリオの宣言的な記述を可能にする
- 統一されたエラーハンドリング（デバイス未接続時はスキップ）
- 協調的キャンセル（stop_flag_refによる中断）
- モジュール追加・変更時の影響範囲を局所化
- **保守性向上: effects.pyを454行から145行に削減（68%削減）**
- **拡張性向上: 新デバイス追加時はハンドラー1ファイル追加のみ**

**呼び出しパターン（リファクタ後）:**
```python
# effects.py (ディスパッチャー)
if cmd_type == 'servo':
    servo_command_handler.handle(cmd, stop_flag_ref)

# servo_command_handler.py (中間層)
speed = command_parser.get_param(cmd, "speed", 0)
speed = command_parser.validate_range(speed, -100, 100, "speed")
command_parser.safe_call(
    servo_rotation_controller.set_speed,
    servo_index, speed,
    error_context=f"Servo #{servo_index}"
)
```

### オンボード機器・システム制御 → 直接呼び出し
**内蔵LED（onboard_led.py）、OLED（oled_patterns.py）、ボリューム制御（volume_control.py）** など、オンボード機器の制御やシステム管理機能は、**必要な箇所から直接呼び出し**されます。

**理由:**
- 必須機能のため利用可能チェックが不要
- システムフィードバック（状態表示）に即座にアクセス
- 複数箇所（loop_controller.py、state_manager.py等）から呼ばれる
- JSONシナリオに含める必要がない補助的機能

**呼び出し例:**
```python
# state_manager.py、loop_controller.pyなど
import onboard_led
import oled_patterns
import volume_control

onboard_led.set_onboard_led(True)
oled_patterns.display_boot_message("Initializing...")
volume_control.read_volume()
```

この設計により、**シナリオで制御する演出機能と、システムを支える基盤機能を明確に分離**できています。

---

## 🎯 主要モジュールの役割

### **effects.py** - コマンドディスパッチャー（145行）
JSONコマンドをパースし、適切なコマンドハンドラーに振り分ける中央集約処理。

**主な関数:**
- `execute_command(command_list, stop_flag_ref)` - コマンドリストを順次実行
- `init()` - ステッピングモーター初期化

**設計:**
- コマンドタイプ判定のみを担当（3層アーキテクチャ）
- JSON解析・バリデーションはcommand_parser.pyに委譲
- 各デバイス固有処理はコマンドハンドラーに委譲

---

### **コマンドハンドラー層** ⭐ NEW
各デバイス・機能ごとのJSONコマンド処理を担当。effects.pyからコマンドを受け取り、パラメータ解析とモジュール呼び出しを実行。

**ハンドラー一覧:**
- **servo_command_handler.py** - サーボモーター（連続回転型/角度制御型自動判別）
- **led_command_handler.py** - NeoPixel LED
- **pwm_led_command_handler.py** - PWM LED（単色LED）
- **motor_command_handler.py** - ステッピングモーター
- **sound_command_handler.py** - DFPlayer Mini

**設計:**
- 各ハンドラーは`handle(cmd, stop_flag_ref)`メソッドを提供
- command_parser.pyの共通機能を利用
- デバイス固有ロジックのみを含む（100-150行程度）

---

### **command_parser.py** - 共通ユーティリティ ⭐ NEW
JSON解析、パラメータ抽出、バリデーション、stop_flag監視など、全コマンドハンドラーで共通する処理。

**主な関数:**
- `get_param(cmd, key, default)` - 安全なパラメータ取得
- `validate_range(value, min, max, name)` - 範囲バリデーション
- `validate_color(color)` - RGBカラーバリデーション
- `check_stop_flag(stop_flag_ref)` - 停止フラグチェック
- `wait_with_stop_check(duration_ms, stop_flag_ref)` - 停止監視付き待機
- `safe_call(func, *args, error_context)` - エラーハンドリング付き関数呼び出し
- `parse_command_type(cmd)` - コマンドタイプ抽出

**設計:**
- コード重複を削減し保守性向上
- fade_controller.py、servo_pwm_utils.pyと同様の共通処理抽出パターン

---

### コア制御モジュール

#### **main.py** - エントリーポイント
- システムの起動点
- 初期化とメインループの開始
- KeyboardInterrupt（Ctrl+C）による正常終了処理

#### **system_init.py** - システム初期化
- 全ハードウェアモジュールの初期化
- scenarios.jsonの読み込み
- 初期化エラーのハンドリングとフォールバック
- 初期化状況をOLEDに表示

#### **loop_controller.py** - メインループ制御
- ボリューム制御のポーリング
- ボタン入力のチェック
- 再生状態の更新
- アイドル自動再生の管理
- エラーハンドリングとリトライ

#### **state_manager.py** - 状態統合調整役（132行）⭐ REFACTORED
- 3つの専門クラスを統合調整
- 既存インターフェース維持（後方互換性）
- セレクトモードの管理
- OLED表示の更新

**責任分離設計（2025-12-22にリファクタ）:**
```
state_manager.py (132行) - 軽量な統合調整役
  ├─ button_handler.py (102行) - ボタン入力処理
  ├─ playback_manager.py (120行) - シナリオ再生管理
  └─ autoplay_controller.py (67行) - 自動再生制御
```

#### **button_handler.py** - ボタン入力処理専用 ⭐ NEW
- 短押し/長押し/ダブルクリック検出
- セレクトモード内の選択変更処理
- イベントベースのボタン状態管理

**主なメソッド:**
- `update(button, select_mode, is_playing)` - ボタン状態更新、イベント検出
- `get_selection_change()` - セレクトモード内のクリック連打検出

#### **playback_manager.py** - シナリオ再生管理専用 ⭐ NEW
- シナリオ再生のスレッド管理
- 再生エラーのハンドリング
- 再生完了コールバック
- 停止フラグ管理

**主なメソッド:**
- `start_scenario(num, dm)` - シナリオ再生開始
- `stop_playback(dm)` - 再生停止
- `is_busy()` - 再生中判定

#### **autoplay_controller.py** - 自動再生制御専用 ⭐ NEW
- アイドルタイムアウト監視
- ワークショップモード制御
- 自動再生タイミング管理

**主なメソッド:**
- `check_autoplay(is_playing, select_mode)` - 自動再生判定
- `on_user_interaction()` - ユーザー操作記録

---

## 🔧 リファクタリング成果（2025-12-22）

### effects.py 大規模リファクタリング
- **削減:** 454行 → 145行（68%削減）
- **分離:** 7種類のコマンドハンドラーに分離（各100-150行）
- **共通化:** command_parser.py（160行）に共通処理を集約

### state_manager.py 責任分離リファクタリング
- **削減:** 296行 → 132行（55%削減）
- **分離:** 3つの専門クラスに分離（button_handler, playback_manager, autoplay_controller）
- **改善:** デバッグ容易性、保守性、テスト容易性が大幅向上

---

## 🎬 コマンド実行フロー

### 1. シナリオ選択からコマンド実行まで

```
ユーザー操作（ボタン押下）
     ↓
state_manager.py
  - ボタン検出
  - シナリオ選択
     ↓
effects.playEffectByNum(scenarios_data, "1", stop_flag_ref)
     ↓
effects.execute_command(command_list, stop_flag_ref)
     ↓
【JSONコマンド解析】
     ↓
各モジュールへ振り分け
```

### 2. effects.py のコマンド解析処理

```python
# コマンド形式の判定
if isinstance(cmd, dict):
    # 辞書形式: {"type": "led", "command": "fade", ...}
    #           {"led_fade_in": {...}}
    cmd_type = cmd.get("type") or next(iter(cmd.keys()))
else:
    # 配列形式: ["effect", "fade", ...]
    #           ["sound", 2, 1]
    cmd_type = cmd[0]

# コマンドタイプに応じて振り分け
if cmd_type == "led":
    → neopixel_controller へ
elif cmd_type == "led_fade_in":
    → pwm_led_controller へ
elif cmd_type == "effect":
    → neopixel_controller へ
elif cmd_type == "sound":
    → sound_patterns へ
elif cmd_type == "motor":
    → stepper_motor へ
elif cmd_type == "delay":
    → time.sleep_ms()
```

---

## 🎨 LED制御の詳細フロー

### NeoPixel（RGB LED）フェード処理

```
scenarios.json
["effect", "fade", [15,16,17], [0,0,0], [255,0,0], 1200]
     ↓
effects.py (259行目)
  - コマンド解析
  - インデックスリスト解決
     ↓
neopixel_controller.fade_global_leds(indices, start_color, end_color, duration_ms, stop_flag_ref)
     ↓
fade_controller.linear_fade(
    start_color,        # [0, 0, 0]
    end_color,          # [255, 0, 0]
    duration_ms,        # 1200
    step_interval_ms,   # 10
    update_callback,    # LEDを更新する関数
    stop_flag_ref       # キャンセル用フラグ
)
     ↓
【10msごとに実行】
  - 進捗率を計算 (0.0 → 1.0)
  - 現在の色を計算（線形補間）
  - update_callback([R, G, B]) を呼び出し
  - NeoPixel.write() でLEDに反映
```

### PWM LED（単色LED）フェード処理

```
scenarios.json
{"led_fade_in": {"led_index": 0, "duration_ms": 1000, "max_brightness": 80}}
     ↓
effects.py (110行目)
  - コマンド解析
  - パラメータ取得
     ↓
pwm_led_controller.fade_pwm_led(led_index, target_brightness, duration_ms, stop_flag_ref)
     ↓
fade_controller.linear_fade(
    start_brightness,   # 現在の輝度（キャッシュから取得）
    target_brightness,  # 80
    duration_ms,        # 1000
    step_interval_ms,   # 10
    update_callback,    # PWMを更新する関数
    stop_flag_ref       # キャンセル用フラグ
)
     ↓
【10msごとに実行】
  - 進捗率を計算 (0.0 → 1.0)
  - 現在の輝度を計算（線形補間）
  - update_callback(brightness) を呼び出し
  - ガンマ補正を適用
  - PWM.duty_u16() でLEDに反映
```

---

## 🔧 ハードウェア制御モジュール

### **neopixel_controller.py** - NeoPixel LED制御
- 複数ストリップ（LV1-LV4）の統合管理
- グローバルインデックスによる全LED制御
- 色キャッシュによる状態管理
- **fade_controller.py を使用した滑らかなフェード処理**

**主な関数:**
- `init_neopixels()` - 初期化
- `set_global_leds_by_indices()` - 単色設定
- `fade_global_leds()` - フェード処理（共通モジュール使用）
- `pattern_off()` - 全消灯

### **pwm_led_controller.py** - PWM LED制御
- 単色LED（GP1-4）の個別制御
- ガンマ補正（γ=2.2）による視覚補正
- 輝度キャッシュによる状態管理
- **fade_controller.py を使用した滑らかなフェード処理**

**主な関数:**
- `init_pwm_leds()` - 初期化
- `set_brightness()` - 輝度設定
- `fade_pwm_led()` - フェード処理（共通モジュール使用）
- `all_off()` - 全消灯

### **fade_controller.py** - 共通フェード処理 ⭐
NeoPixelとPWM LED両方で使用される汎用フェード処理モジュール。

**主な関数:**
- `linear_fade()` - 線形フェード処理
  - 単一数値（PWM輝度）とタプル/リスト（RGB色）の両方に対応
  - 10msステップでの滑らかな変化
  - stop_flag_refによる協調的キャンセル
  - コールバック関数で柔軟な更新処理
- `wait_with_cancel()` - キャンセル可能な待機処理

### **sound_patterns.py** - 音声再生制御
- DFPlayer Mini経由でSDカードから音声再生
- BUSY信号による再生状態管理
- ボリューム制御

### **stepper_motor.py** - ステッピングモーター制御
- 角度指定・ステップ指定での回転
- 速度制御（VERY_SLOW～VERY_FAST）
- 回転方向制御
- 通電解除による安全停止

### **onboard_led.py** - 内蔵LED制御
- Pico 2W Wi-Fiチップ上LEDの制御
- システム状態表示（起動時点滅）
- 再生中の可視化

### **servo_rotation_controller.py** - 連続回転型サーボモーター制御 ⭐
連続回転型サーボモーター（SG90-HV等）の制御モジュール。最大3個のサーボを独立制御。

### **servo_position_controller.py** - 角度制御型サーボモーター制御 ⭐
角度制御型サーボモーター（SG90等）の制御モジュール。最大3個のサーボを独立制御。

### **servo_pwm_utils.py** - サーボ PWM共通ユーティリティ ⭐
servo_rotation_controllerとservo_position_controllerで共有されるPWM変換処理。

**主な関数:**
- `pulse_width_to_duty(pulse_width_us, frequency)` - パルス幅→デューティサイクル変換（16bit）

**設計:**
- fade_controller.pyと同様の共通処理抽出パターン
- コード重複を削減し保守性向上

**主な関数:**
- `init_servos()` - 初期化（GP5-7、50Hz PWM）
- `set_speed(servo_id, speed)` - 速度設定（-100～100、0=停止）
- `rotate_timed(servo_id, speed, duration, stop_flag_ref)` - 時間指定回転
- `stop(servo_id)` - 個別停止
- `stop_all()` - 全停止
- `speed_to_pulse_width(speed)` - 速度→パルス幅変換（1000～2000μs）

**特徴:**
- PWM周波数50Hz固定（サーボモーター標準）
- パルス幅1000μs（CCW）～1500μs（停止）～2000μs（CW）
- 協調的キャンセル対応（stop_flag_ref）

**主な関数:**
- `init_servos()` - 初期化（GP5-7、50Hz PWM）
- `set_angle(servo_id, angle)` - 角度設定（0～180度）
- `move_angle_timed(servo_id, angle, duration, stop_flag_ref)` - 時間指定角度保持
- `center(servo_id)` - 90度中央位置復帰
- `center_all()` - 全サーボ中央復帰
- `angle_to_pulse_width(angle)` - 角度→パルス幅変換（1000～2000μs）

**特徴:**
- PWM周波数50Hz固定
- パルス幅1000μs（0度）～1500μs（90度）～2000μs（180度）
- 協調的キャンセル対応（stop_flag_ref）

**共通設計:**
- PWM変換処理はservo_pwm_utils.pyで共有
- `effects.py`でconfig.pyの`SERVO_TYPES`に基づき自動判別
- `type: "servo"`コマンドで統一的に制御可能
- ステッピングモーター（`stepper_motor.py`）とは独立動作

---

## 🎮 ユーザー入力処理

### ボタン入力の検出フロー

```
loop_controller.py (50msポーリング)
     ↓
state_manager.handle_button_input()
     ↓
ボタン状態の検出
  - 押下時刻の記録
  - 離した時の経過時間計算
     ↓
判定処理
  - 短押し（< 500ms）
  - 長押し（≥ 1000ms）
  - ダブルクリック（500ms以内に2回）
     ↓
モード別処理
  - 通常モード: ランダム再生
  - セレクトモード: シナリオ選択/再生
```

### ボリューム制御フロー

```
loop_controller.py (50msポーリング)
     ↓
volume_control.check_and_update_volume()
     ↓
ADC読み取り（ポテンショメータ）
     ↓
デッドゾーン判定（ノイズ除去）
     ↓
0-30の音量値に変換
     ↓
sound_patterns.set_volume()
     ↓
DFPlayer Mini へコマンド送信
```

---

## 📊 データフロー

### 初期化フロー

```
main.py 起動
     ↓
system_init.init_system()
     ├→ scenarios.json 読み込み
     ├→ hardware_init.init_all()
     │    ├→ DFPlayer Mini 初期化
     │    ├→ OLED 初期化
     │    ├→ NeoPixel 初期化
     │    ├→ PWM LED 初期化
     │    ├→ ステッピングモーター 初期化
     │    └→ 内蔵LED 初期化
     ├→ volume_control.init_volume()
     └→ 初期化状況を OLED に表示
     ↓
loop_controller.start_main_loop()
```

### 再生フロー

```
ボタン押下
     ↓
state_manager.handle_button_input()
     ↓
シナリオ選択
     ↓
effects.playEffectByNum(scenarios_data, num, stop_flag_ref)
     ↓
effects.execute_command(command_list, stop_flag_ref)
     ↓
【コマンドを1つずつ実行】
  ├→ サウンド再生
  ├→ LED点灯/フェード
  ├→ モーター回転
  └→ 待機
     ↓
【stop_flag_refを随時チェック】
  - ボタン押下で中断可能
     ↓
finally: モーター停止
     ↓
再生完了
```

---

## 🛡️ エラーハンドリング

### 階層的エラーハンドリング構造

```
loop_controller.py
  └→ try-except (最上位)
       - KeyboardInterrupt: 正常終了
       - Exception: エラーログとリトライ
       ↓
state_manager.py
  └→ try-except (再生制御)
       - OSError: ハードウェアエラー
       - KeyError: データエラー
       - MemoryError: メモリ不足
       ↓
effects.py
  └→ try-except (コマンド実行)
       - OSError: ハードウェアエラー
       - ValueError: データエラー
       - Exception: 予期しないエラー
       ↓
各モジュール
  └→ try-except (個別処理)
       - 失敗時はフォールバック
       - エラーログ出力
```

### フェールセーフ設計

- **部分的動作継続**: 1つのハードウェアが故障しても他は動作
- **フォールバック**: 初期化失敗時はダミーコントローラで継続
- **協調的キャンセル**: stop_flag_refでユーザー操作に即応
- **クリーンアップ**: finally句でモーター停止など確実に実行

---

## 🔄 設定の一元管理

### **config.py** - 全設定の集約

```python
# ハードウェア設定
UART_TX_PIN = 12
OLED_SDA_PIN = 16
PWM_LED_PINS = [1, 2, 3, 4]
NEOPIXEL_STRIPS = {...}

# タイミング設定
BUTTON_SHORT_PRESS_MS = 500
BUTTON_LONG_PRESS_MS = 1000
IDLE_TIMEOUT_MS = 300000

# PWM LED設定
PWM_LED_FREQUENCY = 1000
PWM_LED_GAMMA = 2.2
PWM_FADE_STEP_INTERVAL_MS = 10
```

すべてのモジュールが `config.py` から設定を読み込むため、カスタマイズが1箇所で完結します。

---

## 📚 関連ドキュメント

- [README.md](./README.md) - プロジェクト概要と使い方
- [HARDWARE_NOTES.md](./HARDWARE_NOTES.md) - ハードウェア接続と仕様
- [CHANGELOG.md](./CHANGELOG.md) - 変更履歴
- [config.py](./config.py) - システム設定

---

## 🎓 コーディング規約とベストプラクティス

### モジュール設計原則

1. **単一責任の原則**: 各モジュールは1つの責務を持つ
2. **依存性の注入**: ハードウェアインスタンスは初期化時に渡す
3. **エラーハンドリング**: 各階層で適切にエラーを処理
4. **ログ出力**: デバッグ情報を適切に出力

### コマンド拡張方法

新しいコマンドを追加する場合：

1. **新規モジュール作成** (例: `new_module.py`)
2. **effects.py にインポート追加**
   ```python
   import new_module
   ```
3. **effects.py のコマンド解析部分に追加**
   ```python
   elif cmd_type == 'new_command':
       new_module.execute(...)
   ```
4. **scenarios.json で使用**
   ```json
   {"type": "new_command", "param": "value"}
   ```

---

このアーキテクチャにより、拡張性が高く保守しやすいシステムを実現しています。
