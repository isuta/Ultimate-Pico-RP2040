"""volume_control.py

PollingVolumeController for both MicroPython and CPython testing.

This module provides a small helper that maps ADC (0-65535) to DFPlayer
volume (0..DFPLAYER_MAX_VOLUME) and applies a deadzone and poll interval.
It avoids direct dependency on MicroPython-only APIs by using fallback
timing functions when running on CPython.
"""

import time


def _now_ms():
    """Return current time in milliseconds.

    Uses time.ticks_ms() if available (MicroPython), otherwise time.time().
    """
    if hasattr(time, 'ticks_ms'):
        return time.ticks_ms()
    return int(time.time() * 1000)


class PollingVolumeController:
    def __init__(self, adc, dfplayer, oled=None, config=None, poll_interval_ms=None, deadzone=None):
        self.adc = adc
        self.dfplayer = dfplayer
        self.oled = oled
        self.config = config or type('C', (), {})()
        self.poll_interval_ms = poll_interval_ms if poll_interval_ms is not None else getattr(self.config, 'VOLUME_POLL_INTERVAL_MS', 100)
        self.deadzone = deadzone if deadzone is not None else getattr(self.config, 'VOLUME_DEADZONE', 1000)

        self._last_adc = None
        self._current_volume = -1
        # set last poll time so first poll runs immediately
        self._last_poll_time = _now_ms() - self.poll_interval_ms

    def init_initial_volume(self):
        if not self.adc:
            return None
        try:
            adc_val = self.adc.read_u16()
        except Exception:
            return None

        maxv = getattr(self.config, 'DFPLAYER_MAX_VOLUME', 30)
        volume = int(adc_val * maxv / 65535)
        volume = max(0, min(volume, maxv))

        self._current_volume = volume
        self._last_adc = adc_val

        if self.dfplayer and getattr(self.dfplayer, 'is_dfplayer_available', lambda: False)():
            try:
                self.dfplayer.set_volume(volume)
            except Exception:
                pass

        return volume

    def poll(self, current_time_ms=None):
        """Poll ADC; return dict with keys: changed, volume, updated_last_user."""
        if not self.adc:
            return {"changed": False, "volume": None, "updated_last_user": False}

        now = current_time_ms if current_time_ms is not None else _now_ms()
        if now - self._last_poll_time < self.poll_interval_ms:
            return {"changed": False, "volume": self._current_volume, "updated_last_user": False}

        self._last_poll_time = now

        try:
            adc_val = self.adc.read_u16()
        except Exception:
            return {"changed": False, "volume": self._current_volume, "updated_last_user": False}

        if self._last_adc is None or abs(adc_val - self._last_adc) > self.deadzone:
            maxv = getattr(self.config, 'DFPLAYER_MAX_VOLUME', 30)
            new_volume = int(adc_val * maxv / 65535)
            new_volume = max(0, min(new_volume, maxv))

            changed = False
            if new_volume != self._current_volume:
                if self.dfplayer and getattr(self.dfplayer, 'is_dfplayer_available', lambda: False)():
                    try:
                        self.dfplayer.set_volume(new_volume)
                    except Exception:
                        pass
                self._current_volume = new_volume
                changed = True

            self._last_adc = adc_val
            return {"changed": changed, "volume": self._current_volume, "updated_last_user": changed}

        self._last_adc = adc_val
        return {"changed": False, "volume": self._current_volume, "updated_last_user": False}

    def get_volume(self):
        return self._current_volume

    def set_volume(self, v):
        maxv = getattr(self.config, 'DFPLAYER_MAX_VOLUME', 30)
        v = max(0, min(int(v), maxv))
        if v != self._current_volume:
            if self.dfplayer and getattr(self.dfplayer, 'is_dfplayer_available', lambda: False)():
                try:
                    self.dfplayer.set_volume(v)
                except Exception:
                    pass
        self._current_volume = v

    @property
    def last_adc(self):
        return self._last_adc
