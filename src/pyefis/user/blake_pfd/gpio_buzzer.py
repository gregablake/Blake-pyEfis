from __future__ import annotations


class GpioBuzzer:
    def __init__(self, pin: int = 18) -> None:
        self.pin = pin
        self.available = False

        try:
            import RPi.GPIO as GPIO  # type: ignore

            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(self.pin, GPIO.OUT)
            self.available = True

        except Exception:
            self.GPIO = None
            self.available = False

    def beep(self) -> None:
        if not self.available:
            print(f"GPIO BUZZER PLACEHOLDER: pin {self.pin}")
            return

        self.GPIO.output(self.pin, True)
        self.GPIO.output(self.pin, False)

    def cleanup(self) -> None:
        if self.available:
            self.GPIO.cleanup(self.pin)