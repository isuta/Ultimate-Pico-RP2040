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
- 短押し：ランダムシナリオを再生  
- アイドル5分後：1分ごとに自動再生

### セレクトモード
起動時に1秒以上ボタンを押し続けると入ります。  
- 短押し1回：次のシナリオを選択  
- 短押し2回：前のシナリオに戻る  
- 長押し：選択中シナリオを再生（モード維持）  
- 再生中の短押し：停止  
- 選択シナリオにはステッピングモーターの動作も含め可能

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

## 🧭 更新履歴
最新の変更履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください.
