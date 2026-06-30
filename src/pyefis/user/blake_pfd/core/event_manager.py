from __future__ import annotations

from pathlib import Path

import yaml
from PyQt6.QtCore import Qt

from pyefis.user.blake_pfd.config_loader import load_config


class EventManager:
    def __init__(self, app) -> None:
        self.app = app

    def handle_key(self, event) -> None:
        current_page = self.app.page_manager.current()

        if current_page == "EMS_ALERTS":
            if event.key() == Qt.Key.Key_A:
                self.app.ems_alert_history.acknowledge_active()
                return

            if event.key() == Qt.Key.Key_S:
                self.app.ems_alert_history.toggle_silence()
                return

        if current_page == "FMS":
            if event.key() == Qt.Key.Key_Up:
                self.app.fms_page.move_selection(-1, self.app.route_manager)
                return

            if event.key() == Qt.Key.Key_Down:
                self.app.fms_page.move_selection(1, self.app.route_manager)
                return

            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                selected = self.app.fms_page.get_selected_waypoint(self.app.route_manager)
                if selected is not None:
                    self.app.activate_direct_to(selected)
                return

        if current_page == "NEAREST":
            nearest = self.app.database.nearest_airports(
                39.1031,
                -84.5120,
                max_results=10,
            )

            if event.key() == Qt.Key.Key_Up:
                self.app.nearest_page.move_selection(-1, nearest)
                return

            if event.key() == Qt.Key.Key_Down:
                self.app.nearest_page.move_selection(1, nearest)
                return

            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                selection = self.app.nearest_page.selected_airport(nearest)
                if selection is not None:
                    _distance_nm, airport = selection
                    self.app.activate_direct_to(airport.ident)
                return

        if current_page == "ENGINE_CHECKLIST":
            if event.key() == Qt.Key.Key_Up:
                self.app.engine_checklist_page.move_selection(-1)
                return

            if event.key() == Qt.Key.Key_Down:
                self.app.engine_checklist_page.move_selection(1)
                return

            if event.key() == Qt.Key.Key_Left:
                self.app.engine_checklist_page.previous_phase()
                return

            if event.key() == Qt.Key.Key_Right:
                self.app.engine_checklist_page.next_phase()
                return

            if event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Space,
            ):
                self.app.engine_checklist_page.toggle_selected()
                return

            if event.key() == Qt.Key.Key_R:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.app.engine_checklist_page.reset_all()
                else:
                    self.app.engine_checklist_page.reset_current_phase()
                return

        if event.key() == Qt.Key.Key_X:
            self.cycle_ems_test_mode()
            return

        key_text = event.text().upper()
        page = self.app.page_manager.from_hotkey(key_text)

        if page is not None:
            self.app.page_manager.set_page(page)

    def cycle_ems_test_mode(self) -> None:
        modes = [
            "normal",
            "high_cht",
            "high_egt",
            "low_oil",
            "alt_fail",
            "ign_fail",
            "low_fuel",
        ]

        current = getattr(self.app.config.ems_test, "mode", "normal")

        try:
            index = modes.index(current)
        except ValueError:
            index = 0

        next_mode = modes[(index + 1) % len(modes)]

        config_path = Path(__file__).parent.parent / "pfd_config.yaml"
        raw = yaml.safe_load(config_path.read_text()) or {}

        raw.setdefault("ems_test", {})
        raw["ems_test"]["mode"] = next_mode

        config_path.write_text(yaml.safe_dump(raw, sort_keys=False))

        self.app.config = load_config()
        self.app.flight_computer.config = self.app.config

        print(f"EMS test mode: {next_mode}")