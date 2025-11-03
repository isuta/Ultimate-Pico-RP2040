"""
Simple display manager wrapper around `oled_patterns`.

Provides a minimal facade so the main program can call `push_message`
without depending directly on the lower-level module. This keeps
main.py tidy and centralizes error handling for OLED operations.
"""

class DisplayManager:
    def __init__(self, oled_patterns):
        self.oled = oled_patterns
        self.last_message = None

    def push_message(self, messages):
        """Push a message to the OLED. `messages` can be a string or list of strings.

        This method swallows OLED errors and logs a warning so the main loop
        keeps running if the display fails.
        """
        try:
            # Normalize single string to list for convenience
            if isinstance(messages, str):
                msgs = [messages]
            else:
                msgs = messages
            self.oled.push_message(msgs)
            self.last_message = msgs
        except Exception as e:
            print(f"Warning: OLED push failed: {e}")
