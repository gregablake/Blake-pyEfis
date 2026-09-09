from __future__ import annotations

from types import SimpleNamespace

from pyefis.user.blake_pfd.obstacles import (
    Obstacle,
    ObstacleState,
)
from pyefis.user.blake_pfd.pfd_demo import (
    BlakePfdDemo,
)


def make_obstacle_state() -> ObstacleState:
    return ObstacleState(
        ok=True,
        nearby=[
            Obstacle(
                ident="TEST-TOWER",
                lat_deg=39.0,
                lon_deg=-84.0,
                elevation_ft=1200.0,
                height_agl_ft=300.0,
                distance_nm=1.5,
                bearing_deg=15.0,
            )
        ],
        warning=False,
    )


def make_fresh_watchdog():
    return SimpleNamespace(
        position_valid=True,
        position_fresh=True,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )


def test_synthetic_obstacle_draw_uses_live_flight_inputs(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.sensor_watchdog_state = (
        make_fresh_watchdog()
    )

    state = make_obstacle_state()

    pfd = SimpleNamespace(
        indicated_alt_ft=1350.0,
        heading_deg=22.0,
        pitch_deg=3.0,
        roll_deg=-4.0,
    )

    captured = {}

    class FakeProjector:
        def project(
            self,
            **kwargs,
        ):
            captured.update(
                kwargs
            )
            return []

    widget.obstacle_projection_computer = (
        FakeProjector()
    )

    widget.draw_synthetic_obstacles(
        None,
        pfd,
        state,
        1024,
        600,
    )

    assert (
        captured["obstacles"]
        is state.nearby
    )

    assert (
        captured["aircraft_alt_ft"]
        == pfd.indicated_alt_ft
    )

    assert (
        captured["heading_deg"]
        == pfd.heading_deg
    )

    assert (
        captured["pitch_deg"]
        == pfd.pitch_deg
    )

    assert (
        captured["roll_deg"]
        == pfd.roll_deg
    )

    assert captured["width_px"] == 1024
    assert captured["height_px"] == 600

    widget.close()


def test_synthetic_obstacles_fail_closed_when_position_stale(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.sensor_watchdog_state = (
        SimpleNamespace(
            position_valid=True,
            position_fresh=False,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=True,
        )
    )

    class MustNotProject:
        def project(
            self,
            **kwargs,
        ):
            raise AssertionError(
                "stale position must not project obstacles"
            )

    widget.obstacle_projection_computer = (
        MustNotProject()
    )

    widget.draw_synthetic_obstacles(
        None,
        widget.pfd,
        make_obstacle_state(),
        1024,
        600,
    )

    widget.close()


def test_synthetic_obstacles_do_not_project_unavailable_state(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.sensor_watchdog_state = (
        make_fresh_watchdog()
    )

    class MustNotProject:
        def project(
            self,
            **kwargs,
        ):
            raise AssertionError(
                "unavailable obstacle data must not project"
            )

    widget.obstacle_projection_computer = (
        MustNotProject()
    )

    state = ObstacleState(
        ok=False,
        nearby=[],
        warning=False,
    )

    widget.draw_synthetic_obstacles(
        None,
        widget.pfd,
        state,
        1024,
        600,
    )

    widget.close()


def test_synthetic_vision_draw_order_places_obstacles_after_runway(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    calls = []

    widget.draw_synthetic_terrain = (
        lambda *args, **kwargs:
        calls.append("terrain")
    )

    widget.draw_synthetic_runway = (
        lambda *args, **kwargs:
        calls.append("runway")
    )

    widget.draw_synthetic_obstacles = (
        lambda *args, **kwargs:
        calls.append("obstacles")
    )

    widget.synthetic_vision.update = (
        lambda pfd:
        SimpleNamespace(
            objects=[],
        )
    )

    widget.draw_synthetic_vision(
        None,
        widget.pfd,
        1024,
        600,
        obstacle_state=(
            make_obstacle_state()
        ),
    )

    assert calls == [
        "terrain",
        "runway",
        "obstacles",
    ]

    widget.close()


def test_synthetic_obstacles_use_runtime_warning_thresholds(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.sensor_watchdog_state = (
        make_fresh_watchdog()
    )

    pfd = SimpleNamespace(
        indicated_alt_ft=2000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    captured = {}

    class FakeProjector:
        def project(
            self,
            **kwargs,
        ):
            captured.update(
                kwargs
            )
            return []

    widget.obstacle_projection_computer = (
        FakeProjector()
    )

    widget.draw_synthetic_obstacles(
        None,
        pfd,
        make_obstacle_state(),
        1024,
        600,
    )

    assert (
        captured["warning_distance_nm"]
        == widget.obstacles.warning_distance_nm
    )

    assert (
        captured["warning_clearance_ft"]
        == widget.obstacles.warning_clearance_ft
    )

    widget.close()



def test_synthetic_obstacle_colors_are_per_object(
    qtbot,
    tmp_path,
):
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.sensor_watchdog_state = (
        make_fresh_watchdog()
    )

    pfd = SimpleNamespace(
        indicated_alt_ft=2000.0,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    class FakeProjector:
        def project(
            self,
            **kwargs,
        ):
            return [
                SimpleNamespace(
                    ident="THREAT",
                    x_px=400.0,
                    y_px=250.0,
                    threat=True,
                ),
                SimpleNamespace(
                    ident="SAFE",
                    x_px=600.0,
                    y_px=250.0,
                    threat=False,
                ),
            ]

    widget.obstacle_projection_computer = (
        FakeProjector()
    )

    pen_colors = []

    class FakePainter:
        def save(self):
            pass

        def restore(self):
            pass

        def setBrush(
            self,
            brush,
        ):
            pass

        def setPen(
            self,
            pen,
        ):
            color = pen.color()

            pen_colors.append(
                (
                    color.red(),
                    color.green(),
                    color.blue(),
                )
            )

        def drawPolygon(
            self,
            polygon,
        ):
            pass

        def drawLine(
            self,
            start,
            end,
        ):
            pass

    widget.draw_synthetic_obstacles(
        FakePainter(),
        pfd,
        make_obstacle_state(),
        1024,
        600,
    )

    assert pen_colors == [
        (
            255,
            0,
            0,
        ),
        (
            255,
            220,
            0,
        ),
    ]

    widget.close()
