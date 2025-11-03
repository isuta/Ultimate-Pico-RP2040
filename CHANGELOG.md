# Changelog

本ファイルでは、プロジェクトの主要な変更履歴を記録します。

---

## [2025-11-03]
### 状態管理・モード制御ロジックの刷新
`state_manager.py` と `system_init.py` を導入し、システム構造を再設計。

- **主な変更点**
  - `system_init.py`: 全ハードウェアおよびモジュールの初期化を一括管理。構成情報を `config.py` から取得。
  - `state_manager.py`: ボタン入力、再生制御、OLED表示、アイドル状態管理を統合。
  - `main.py`: イベントループ主体の軽量設計に変更し、状態更新 (`update_playback`, `check_idle_autoplay`) のみを実行。
  - セレクトモード改良：シナリオ選択後もモードが維持され連続再生が可能に。
  - 通常モードとアイドル自動再生が安定化。

---

## [2025-11-01]
### main.py のスリム化と表示・初期化ロジックの分割

- **追加モジュール**
  - `volume_control.py`: ボリューム制御（ADC→DFPlayer反映）
  - `hardware_init.py`: 各ハードウェア初期化
  - `display_manager.py`: OLED出力の一元化
  - `onboard_led.py`: 内蔵LED制御（状態表示・デバッグ用途）
  - `system_init.py`: システム全体の初期化統合（NEW）
  - `state_manager.py`: モード・再生・ボタン統合管理（NEW）

---

### 🧩 管理ルール
- **README.md** はシステム概要・使い方中心に保つ。  
- **CHANGELOG.md** は技術的な変更履歴とリリース記録を集約。  
- 各リリースは `[YYYY-MM-DD]` 形式でセクションを追加。
