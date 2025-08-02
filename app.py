from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QCheckBox, QGroupBox
from PyQt6.QtCore import Qt
import sys
import threading
import main  # Імпорт основного синтезатора


class SynthWindow(QWidget):
    def closeEvent(self, event):
        # Зупиняємо таймер оновлення нот
        if hasattr(self, 'timer') and self.timer.is_alive():
            self.timer.cancel()

        # Правильно зупиняємо синтезатор
        main.stop_synth()
        event.accept()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pyano Synth')
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()

        # Запуск аудіо-стріму
        main.RUNNING[0] = True
        main.start_keyboard_listener()  # Запускаємо listener клавіш
        main.run_synth_background()

        # Гучність
        vol_group = QGroupBox('Volume')
        vol_layout = QHBoxLayout()
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setMinimum(0)
        self.vol_slider.setMaximum(100)
        self.vol_slider.setValue(int(main.AMPLITUDE[0]*100))
        self.vol_slider.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.vol_slider)
        vol_group.setLayout(vol_layout)
        layout.addWidget(vol_group)

        # Вибір хвилі
        wave_group = QGroupBox('Wave Type')
        wave_layout = QHBoxLayout()
        self.wave_buttons = {}
        for wave in ['sine', 'square', 'triangle', 'sawtooth']:
            btn = QPushButton(wave.capitalize())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, w=wave: self.set_wave(w))
            wave_layout.addWidget(btn)
            self.wave_buttons[wave] = btn
        wave_group.setLayout(wave_layout)
        layout.addWidget(wave_group)
        self.update_wave_buttons()

        # Ефекти
        fx_group = QGroupBox('Effects')
        fx_layout = QHBoxLayout()
        self.reverb_cb = QCheckBox('Reverb')
        self.chorus_cb = QCheckBox('Chorus')
        self.delay_cb = QCheckBox('Delay')
        self.reverb_cb.setChecked(main.REVERB_ON[0])
        self.chorus_cb.setChecked(main.CHORUS_ON[0])
        self.delay_cb.setChecked(main.DELAY_ON[0])
        self.reverb_cb.stateChanged.connect(self.toggle_reverb)
        self.chorus_cb.stateChanged.connect(self.toggle_chorus)
        self.delay_cb.stateChanged.connect(self.toggle_delay)
        fx_layout.addWidget(self.reverb_cb)
        fx_layout.addWidget(self.chorus_cb)
        fx_layout.addWidget(self.delay_cb)
        fx_group.setLayout(fx_layout)
        layout.addWidget(fx_group)

        # Активні ноти
        self.notes_label = QLabel('Notes: (none)')
        layout.addWidget(self.notes_label)

        self.setLayout(layout)
        # Оновлення нот
        self.timer = threading.Timer(0.1, self.update_notes)
        self.timer.start()

    def set_volume(self, value):
        main.AMPLITUDE[0] = value / 100.0

    def set_wave(self, wave):
        main.WAVE_TYPE[0] = wave
        self.update_wave_buttons()
        main.phase = 0

    def update_wave_buttons(self):
        for w, btn in self.wave_buttons.items():
            btn.setChecked(main.WAVE_TYPE[0] == w)

    def toggle_reverb(self, state):
        main.REVERB_ON[0] = bool(state)
        main.reverb_buffer[:] = 0

    def toggle_chorus(self, state):
        main.CHORUS_ON[0] = bool(state)
        main.chorus_buffer[:] = 0

    def toggle_delay(self, state):
        main.DELAY_ON[0] = bool(state)
        main.delay_buffer[:] = 0

    def update_notes(self):
        if not main.RUNNING[0]:  # Якщо програма закривається, не оновлювати
            return

        notes = main.last_debug.get('notes', [])
        if notes:
            self.notes_label.setText(
                'Notes: ' + ', '.join(str(round(n, 2)) for n in notes))
        else:
            self.notes_label.setText('Notes: (none)')

        # Використовуємо QTimer замість threading.Timer для кращої інтеграції з Qt
        if main.RUNNING[0]:
            self.timer = threading.Timer(0.1, self.update_notes)
            self.timer.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SynthWindow()
    window.show()
    sys.exit(app.exec())
