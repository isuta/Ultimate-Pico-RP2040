# データ駆動型 統合制御システム (NeoPixel/OLED/DFPlayer Mini/Stepper Motor)

このプロジェクトは、MicroPython環境（ESP32/ESP8266/RP2040など）で動作する、データ駆動型の統合制御システムです。  
LED、OLEDディスプレイ、オーディオ再生（DFPlayer Mini）、およびステッピングモーターの制御を、`scenarios.json` ファイルに基づいて実行します。

---

## 🚀 システム概要

このシステムは、ハードウェアの配線や設定を `config.py` に集約し、変更に強い構成を実現しています。  
複数のモジュールが独立して動作するため、一部ハードウェアが未接続でもシステムは動作を継続します。

| モジュール | 役割 |
| ----- | ----- |
| **NeoPixel** | 抽選結果やアニメーションの光演出 |
| **OLED (SSD1306)** | ステータスや選択シナリオの表示 |
| **DFPlayer Mini** | 効果音/BGM再生 |
| **ステッピングモーター** | ギミックや機構制御、角度・ステップ単位で動作 |
| **タクトスイッチ** | 抽選・モード切替・シナリオ選択 |
| **内蔵LED** | システム状態や再生中を可視化 |
| **ポテンショメータ** | アナログボリューム制御 |

---

## ⚙️ セットアップ

### 必要ファイル
デバイスのルートに以下を配置：
```
main.py
config.py
effects.py
led_patterns.py
oled_patterns.py
sound_patterns.py
onboard_led.py
hardware_init.py
display_manager.py
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

### ボタン操作のカスタマイズ
`config.py` でボタンの反応速度を調整できます:
- `BUTTON_SHORT_PRESS_MS`: 短押し判定時間（デフォルト: 500ms）
- `BUTTON_LONG_PRESS_MS`: 長押し判定時間（デフォルト: 1000ms）
- `BUTTON_DOUBLE_CLICK_INTERVAL_MS`: ダブルクリック判定間隔（デフォルト: 500ms）

---

## 🔧 トラブルシューティング

| 症状 | 対応 |
|------|------|
| OLEDが表示しない | コンソール出力で状態確認 |
| DFPlayerが鳴らない | TX/RX配線と電源を確認 |
| LEDが点灯しない | ストリップ設定とピン番号を確認 |
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

## 🧭 更新履歴
最新の変更履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください。
