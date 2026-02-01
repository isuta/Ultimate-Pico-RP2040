# データ駆動型 統合制御システム (NeoPixel/OLED/DFPlayer Mini/Stepper Motor)

このプロジェクトは、MicroPython環境（ESP32/ESP8266/RP2040など）で動作する、データ駆動型の統合制御システムです。  
LED、OLEDディスプレイ、オーディオ再生（DFPlayer Mini）、およびステッピングモーターの制御を、`scenarios.json` ファイルに基づいて実行します。

---

## 🚀 システム概要

このシステムは、ハードウェアの配線や設定を `config.py` に集約し、変更に強い構成を実現しています。  
複数のモジュールが独立して動作するため、一部ハードウェアが未接続でもシステムは動作を継続します。

| モジュール | 役割 |
| ----- | ----- |
| **NeoPixel** | 抽選結果やアニメーションの光演出（RGB LEDストリップ、WS2812B） |
| **PWM LED** | 単色LEDの輝度制御、フェード演出（GP1-4、最大4個、ガンマ補正対応） |
| **サーボモーター** | 連続回転サーボ制御、速度・時間指定（GP5-7、最大3個、SG90-HV等） |
| **OLED (SSD1306)** | ステータスや選択シナリオの表示 |
| **DFPlayer Mini** | 効果音/BGM再生 |
| **ステッピングモーター** | ギミックや機構制御、角度・ステップ単位で動作 |
| **タクトスイッチ** | 抽選・モード切替・シナリオ選択 |
| **内蔵LED** | システム状態や再生中を可視化（Pico 2W専用） |
| **ポテンショメータ** | アナログボリューム制御 |

### 💡 想定用途
- **イベント・展示の演出装置**: 光と音を組み合わせた自動演出
- **インタラクティブアート作品**: ボタン操作に応じた視覚・聴覚表現
- **ガチャガチャ/抽選機のエフェクト**: ランダム再生と物理ギミックの連動
- **教育用IoTプロジェクト**: センサーやアクチュエータの統合制御学習

### ✨ システムの特徴
- **プログラミング知識不要**: JSONファイルを編集するだけで新しい演出を追加可能
- **堅牢な設計**: エラーハンドリングにより、商用利用にも耐える安定性
- **非同期処理**: シナリオ再生中もボタン操作やボリューム調整が可能
- **柔軟なカスタマイズ**: `config.py`で全ての動作パラメータを調整可能
- **豊富な実例**: すぐに試せるテストシナリオを含む `scenarios.json` が付属
- **柔軟な拡張性**: モジュール設計により、新しいハードウェアや機能を簡単に追加可能

## 📚 ドキュメント

- **[MODES.md](./MODES.md)** - モード一覧と操作方法（通常/セレクト/ワークショップモード）
- **[SCENARIO_GUIDE.md](./SCENARIO_GUIDE.md)** - シナリオ作成ガイド（コマンドリファレンス、実践例）
- **[CONFIGURATION.md](./CONFIGURATION.md)** - 設定ガイド（config.py、カスタマイズ方法）
- **[HARDWARE_NOTES.md](./HARDWARE_NOTES.md)** - ハードウェア接続ガイド
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - システムアーキテクチャ
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - 開発ガイドライン
- **[CHANGELOG.md](./CHANGELOG.md)** - 変更履歴
- **[TESTING.md](./TESTING.md)** - テストガイド（詳細なテスト説明）

---

## ⚙️ セットアップ

### ⚠️ ハードウェア接続の注意事項

**LED接続時は必ず電流制限抵抗を使用してください。** 詳細は [HARDWARE_NOTES.md](./HARDWARE_NOTES.md) を参照してください。

### 必要ファイル
デバイスのルートに以下を配置：
```
main.py
config.py
effects.py
command_parser.py
servo_command_handler.py
led_command_handler.py
pwm_led_command_handler.py
motor_command_handler.py
sound_command_handler.py
fade_controller.py
neopixel_controller.py
pwm_led_controller.py
servo_rotation_controller.py
servo_position_controller.py
servo_pwm_utils.py
oled_patterns.py
sound_patterns.py
onboard_led.py
hardware_init.py
display_manager.py
state_manager.py
button_handler.py
playback_manager.py
autoplay_controller.py
volume_control.py
system_init.py
state_manager.py
loop_controller.py
stepper_motor.py
scenarios.json
```

ライブラリは `lib` フォルダに配置：
```
ssd1306.py
neopixel.py
```

### ハードウェア設定
`config.py` を編集して、各ピンや設定値を環境に合わせて調整してください。  
ステッピングモーターを追加した場合は、`stepper_motor.py` 内の初期化ピンとモーター仕様も設定してください。

### 動作環境
- **MicroPythonバージョン**: v1.20以降推奨（最低v1.19）
- **対応ボード**: Raspberry Pi Pico / Pico W / Pico 2 / Pico 2W / Ultimate RP2040
- **メモリ**: 長時間動作時は定期的な再起動を推奨

---

## 📖 シナリオの作成

`scenarios.json` でLED、サウンド、モーターの動作を組み合わせた演出を定義できます。

### ⚠️ 重要: シナリオ名の命名規則

**ランダム再生対象にするシナリオは、必ず数字で始まる名前を付けてください。**

- **ランダム再生される**: `"1"`, `"2"`, `"901"`, `"_test"` など（数字またはアンダースコア+数字で始まる）
- **ランダム再生されない**: `"test_servo_basic"`, `"demo_effect"` など（文字で始まる）

この規則は通常モードとワークショップモードの両方に適用されます。
ワークショップモードでランダム再生させたい場合も、シナリオ名を数字にする必要があります。

**例:**
```json
{
    "901": [  // ✅ ランダム再生される
        {"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000}
    ],
    "test_servo": [  // ❌ ランダム再生されない（手動選択のみ）
        {"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000}
    ]
}
```

### シナリオ例
```json
"combined_effect": [
    ["sound", 2, 1],
    {"type": "led", "command": "fade", "strip": "all", "start_color": [0, 0, 0], "end_color": [255, 0, 0], "duration": 1000},
    {"led_fade_in": {"led_index": 0, "duration_ms": 500, "max_brightness": 80}},
    {"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000},
    {"type": "motor", "command": "rotate", "angle": 90, "speed": "SLOW", "direction": 1},
    ["delay", 2000],
    {"type": "led", "command": "off"}
]
```

### 主要コマンド一覧

| カテゴリ | コマンド例 | 説明 |
|---------|-----------|------|
| **サウンド** | `["sound", 2, 1]` | `/02/001.mp3`を再生 |
| **NeoPixel** | `{"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0]}` | RGB LEDストリップを赤色に |
| **PWM LED** | `{"led_fade_in": {"led_index": 0, "duration_ms": 1000, "max_brightness": 80}}` | 単色LEDをフェードイン |
| **サーボ** | `{"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000}` | サーボを2秒間回転 |
| **ステッピング** | `{"type": "motor", "command": "rotate", "angle": 90, "speed": "SLOW", "direction": 1}` | モーターを90度回転 |
| **待機** | `["delay", 1000]` または `{"wait_ms": 1000}` | 1秒待機 |
| **繰り返し** | `{"type": "repeat", "count": 10, "commands": [...]}` | コマンド群を繰り返す（0で無限ループ） |

**📘 詳細なコマンドリファレンスは [SCENARIO_GUIDE.md](./SCENARIO_GUIDE.md) を参照してください。**

---

## 🎮 モード操作

### 通常モード
起動後に「Push the button」と表示されます。  
- **短押し**：ランダムシナリオを再生  
- **アイドル時の自動再生**：
  - 5分間（デフォルト）操作がないとアイドル状態に移行
  - その後、1分ごと（デフォルト）にランダムシナリオを自動再生
  - `config.py` で調整可能:
    - `IDLE_TIMEOUT_MS`: アイドル移行までの時間（ミリ秒）
    - `AUTO_PLAY_INTERVAL_SECONDS`: 自動再生の間隔（秒）

### セレクトモード
起動時に1秒以上ボタンを押し続けると入ります。  
- **短押し1回**：次のシナリオを選択  
- **短押し2回**：前のシナリオに戻る  
- **長押し**：選択中シナリオを再生（モード維持）  
- **再生中の短押し**：停止  
- 選択シナリオにはステッピングモーターの動作も含め可能

### ワークショップモード
`config.py`で`WORKSHOP_MODE = True`に設定すると、起動直後から連続自動再生を開始します。

**📘 全モードの詳細な操作方法・設定方法は [MODES.md](./MODES.md) を参照してください。**  
**📘 タイミング設定の詳細は [CONFIGURATION.md](./CONFIGURATION.md) を参照してください。**

---

## 🔧 トラブルシューティング

| 症状 | 対応 |
|------|------|
| OLEDが表示しない | コンソール出力で状態確認 |
| DFPlayerが鳴らない | TX/RX配線と電源を確認 |
| NeoPixelが点灯しない | ストリップ設定とピン番号を確認 |
| PWM LEDが点灯しない | 抵抗（150-330Ω）とGP1-4のピン配線、LED極性を確認 |
| モーターが動かない | `stepper_motor.py` 初期化と配線確認 |
| ボタン無反応 | コンソール専用モードに自動移行 |
| 全未接続 | 内蔵LEDとログで確認可能 |

---

## 📋 起動時ログ例
```
=== System Ready ===
Button: Available / Console Mode
OLED: Available
Audio: Available
LED: Available
Stepper Motor: Available
Onboard LED: Available
Volume Control: Available
===================
```

### デバッグ情報
- 各モジュールの初期化状況がシリアルモニタに表示されます
- エラー発生時はスタックトレースが出力されます
- OLED画面にもエラータイプ（"Hardware Error"等）が表示されます

---

## 🛍️ 利用可能な機器の紹介 (ハードウェア購入リンク)

このシステムを動作させるために一般的に使用される主要なハードウェア（開発ボード、モジュールなど）の一部を以下に紹介します。

**💡 注意:** 以下のリンクには、開発者に少額の報酬が発生する**アフィリエイトリンク**が含まれています。製品の選定や購入は、ご自身の判断と責任で行ってください。

* **推奨開発ボード（rp2040系またはその互換）**
    * [Raspberry Pi Pico 2 W](https://amzn.to/4ouwNfG)
    * [Raspberry Pi Pico W](https://amzn.to/47F1xn7)
    * [Ultimate RP2040](https://amzn.to/47YsYcI)
    * [Raspberry Pi Pico2 / Pico 2H / Pico 2W / Pico 2WH ラズベリーパイ マイクロ コントローラー RP2350 技適有り](https://a.r10.to/hYeG9P)
* **OLEDディスプレイ（OLEDモジュール SSD1306）**
    * [Hailege 0.96" SSD1306 I2C IIC OLED LCDディスプレイ128X64](https://amzn.to/43hmR0t)
    * [4ピンヘッダー付 1.3インチ 128 x 64 IIC I 2 C SPIシリアル OLEDディスプレイモジュール ホワイトテキストカラー ホワイトOLEDモジュール](https://a.r10.to/hkBkDg)
* **オーディオモジュール（例: DFPlayer Mini）**
    * [DFRobot DFPlayer - ミニMP3プレーヤー](https://amzn.to/4hPtRrE)
    * [Dfplayer-ミニmp3プレーヤーモジュール](https://a.r10.to/hgNip6)
* **NeoPixel LEDストリップ**
    * [BTF-LIGHTING WS2812B LEDテープライト 5050 SMD RGBIC 合金ワイヤー 1m 60LEDs](https://amzn.to/43UiXe9)
    * [BTF-LIGHTING LEDイルミネーション WS2811 LEDテープライト RGB5050 アドレス可能 ドリームカラー 5M 300LEDs](hhttps://amzn.to/49E9Zp3)
    * [BTF-LIGHTING WS2812B LEDテープライト 5050 SMD RGBIC 合金ワイヤー 1m 60LEDs](https://amzn.to/4nCNWTa)
    * [ALITOVE WS2812B LEDテープ1m 144連 NeoPixel RGB TAPE LED](https://amzn.to/4nAmqWl)
    * [LEDテープライト 5050 SMD 合金ワイヤー 1m 144LEDs](https://a.r10.to/hYNCkq)
    * [BTF-LIGHTING WS2812B LEDテープライト 5050 SMD RGBIC 合金ワイヤー 1m 60LEDs](https://a.r10.to/h5qeK3)

---

## 🧪 テスト

このプロジェクトには、**PC上で実行可能な単体テスト**が含まれています。  
Picoに転送する前にロジックの正当性を検証でき、開発速度が大幅に向上します。

### テストスイート

| テストファイル | 内容 | テスト数 |
|---------------|------|----------|
| `test_command_parser.py` | コマンド解析ロジックの検証 | 36件 |
| `test_logger.py` | ログレベルフィルタリングの検証 | 20件 |
| `test_scenarios_validator.py` | scenarios.json形式チェック | 104件 |

**総計: 160件のテスト・チェック項目**

### クイックスタート

```bash
# すべてのテストを実行
python tests/test_command_parser.py && python tests/test_logger.py && python tests/test_scenarios_validator.py

# 個別に実行
python tests/test_command_parser.py
```

### 詳細情報

テストの詳細な説明、実行方法、追加方法については [TESTING.md](./TESTING.md) を参照してください。



