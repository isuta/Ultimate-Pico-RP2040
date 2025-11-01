"""Simple local test for volume_control.PollingVolumeController

This test uses mocks for ADC and DFPlayer to validate:
- init_initial_volume() maps ADC -> volume and calls set_volume
- poll() respects deadzone and calls set_volume only when volume changes

Run with CPython (not MicroPython):
  python .\test_volume_control.py
"""
import time
import volume_control


class MockADC:
    def __init__(self, values):
        self.values = list(values)
        self.i = 0

    def read_u16(self):
        v = self.values[self.i % len(self.values)]
        self.i += 1
        return v


class MockDF:
    def __init__(self):
        self.vol = None
        self.available = True

    def is_dfplayer_available(self):
        return self.available

    def set_volume(self, v):
        print(f"MockDF.set_volume({v})")
        self.vol = v


class Cfg:
    DFPLAYER_MAX_VOLUME = 30
    VOLUME_DEADZONE = 1000
    VOLUME_POLL_INTERVAL_MS = 10


def run_tests():
    print('--- test: init_initial_volume ---')
    # ADC returns a mid value -> expect mid volume
    adc = MockADC([32767])
    df = MockDF()
    vc = volume_control.PollingVolumeController(adc, df, oled=None, config=Cfg, poll_interval_ms=0, deadzone=Cfg.VOLUME_DEADZONE)
    init_v = vc.init_initial_volume()
    print('init_v=', init_v, 'df.vol=', df.vol)
    assert init_v == df.vol == int(32767 * Cfg.DFPLAYER_MAX_VOLUME / 65535)

    print('--- test: poll with no meaningful change (inside deadzone) ---')
    # Give an ADC value close to previous -> inside deadzone
    adc = MockADC([vc.last_adc + 100])
    vc.adc = adc
    res = vc.poll(int(time.time()*1000))
    print('res=', res)
    assert res['changed'] is False

    print('--- test: poll with change beyond deadzone ---')
    # Use value far from last to trigger set_volume
    large_adc = max(0, (vc.last_adc or 0) + Cfg.VOLUME_DEADZONE + 5000)
    adc = MockADC([large_adc])
    vc.adc = adc
    res = vc.poll(int(time.time()*1000))
    print('res=', res, 'df.vol=', df.vol)
    assert res['changed'] is True

    print('\nAll tests passed (logical checks).')


if __name__ == '__main__':
    run_tests()
