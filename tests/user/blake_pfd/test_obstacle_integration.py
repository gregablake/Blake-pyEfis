from pathlib import Path

from pyefis.user.blake_pfd.obstacle_database import (
    ObstacleDatabase,
    ObstacleDatabaseBuilder,
)
from pyefis.user.blake_pfd.obstacle_runtime import (
    ObstacleRuntimeProvider,
)
from pyefis.user.blake_pfd.core.obstacle_projection import (
    ObstacleProjectionComputer,
)


HEADER = (
    "OAS,VERIFIED STATUS,COUNTRY,STATE,CITY,"
    "LATDEC,LONDEC,DMSLAT,DMSLON,TYPE,"
    "QUANTITY,AGL,AMSL,LIGHTING,ACCURACY,"
    "MARKING,FAA STUDY,ACTION,JDATE\n"
)


def test_faa_csv_reaches_runtime_and_synthetic_projection(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DOF.CSV"
    database_path = tmp_path / "obstacles.sqlite"

    # About 1.6 NM east of KHAO.
    # At 700 FT MSL with ownship at 1500 FT,
    # this should be a RED obstacle threat.
    source.write_text(
        HEADER
        + (
            "39-TEST001,O,US,OH,HAMILTON,"
            "39.363800,-84.505500,"
            ",,TOWER,1,"
            "00100,00700,R,5D,M,"
            "TEST,C,2026260\n"
        ),
        encoding="cp1252",
    )

    count = ObstacleDatabaseBuilder().build(
        source,
        database_path,
    )

    assert count == 1

    database = ObstacleDatabase(
        database_path,
        now_provider=lambda: (
            source.stat().st_mtime
        ),
    )

    provider = ObstacleRuntimeProvider(
        database
    )

    state = provider.update(
        aircraft_lat=39.3638,
        aircraft_lon=-84.5400,
        aircraft_alt_ft=1500.0,
    )

    assert state.ok is True
    assert state.warning is True
    assert state.nearby is not None
    assert len(state.nearby) == 1
    assert (
        state.nearby[0].ident
        == "39-TEST001"
    )

    projected = (
        ObstacleProjectionComputer().project(
            obstacles=state.nearby,
            aircraft_alt_ft=1500.0,
            heading_deg=92.0,
            pitch_deg=0.0,
            roll_deg=0.0,
            width_px=1024,
            height_px=600,
            warning_distance_nm=(
                provider.warning_distance_nm
            ),
            warning_clearance_ft=(
                provider.warning_clearance_ft
            ),
        )
    )

    assert len(projected) == 1

    obstacle = projected[0]

    assert obstacle.ident == "39-TEST001"
    assert obstacle.threat is True

    assert 0.0 <= obstacle.x_px <= 1024.0
    assert 0.0 <= obstacle.y_px <= 600.0


def test_faa_csv_threat_reaches_pfd_obstacle_painter(
    qtbot,
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    from pyefis.user.blake_pfd.pfd_demo import (
        BlakePfdDemo,
    )

    source = tmp_path / "DRAW_DOF.CSV"
    database_path = (
        tmp_path
        / "draw_obstacles.sqlite"
    )

    source.write_text(
        HEADER
        + (
            "39-DRAW001,O,US,OH,HAMILTON,"
            "39.363800,-84.505500,"
            ",,TOWER,1,"
            "00100,00700,R,5D,M,"
            "TEST,C,2026260\n"
        ),
        encoding="cp1252",
    )

    count = ObstacleDatabaseBuilder().build(
        source,
        database_path,
    )

    assert count == 1

    database = ObstacleDatabase(
        database_path,
        now_provider=lambda: (
            source.stat().st_mtime
        ),
    )

    provider = ObstacleRuntimeProvider(
        database
    )

    state = provider.update(
        aircraft_lat=39.3638,
        aircraft_lon=-84.5400,
        aircraft_alt_ft=1500.0,
    )

    assert state.ok is True
    assert state.warning is True
    assert len(state.nearby or []) == 1

    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.obstacles = provider

    widget.obstacle_projection_computer = (
        ObstacleProjectionComputer()
    )

    widget.sensor_watchdog_state = (
        SimpleNamespace(
            position_valid=True,
            position_fresh=True,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=True,
        )
    )

    pfd = SimpleNamespace(
        indicated_alt_ft=1500.0,
        heading_deg=92.0,
        pitch_deg=0.0,
        roll_deg=0.0,
    )

    pen_colors = []
    polygons = []
    lines = []

    class CapturePainter:
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
            polygons.append(
                polygon
            )

        def drawLine(
            self,
            start,
            end,
        ):
            lines.append(
                (
                    start,
                    end,
                )
            )

    widget.draw_synthetic_obstacles(
        CapturePainter(),
        pfd,
        state,
        1024,
        600,
    )

    red = (
        255,
        0,
        0,
    )

    assert red in pen_colors
    assert len(polygons) == 1
    assert len(lines) == 1

    widget.close()


def test_faa_csv_threat_reaches_full_pfd_render(
    qtbot,
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from PyQt6.QtGui import (
        QImage,
        QPainter,
    )

    from pyefis.user.blake_pfd.pfd_demo import (
        BlakePfdDemo,
    )

    source = tmp_path / "FULL_RENDER_DOF.CSV"
    database_path = (
        tmp_path
        / "full_render_obstacles.sqlite"
    )

    source.write_text(
        HEADER
        + (
            "39-FULL001,O,US,OH,HAMILTON,"
            "39.363800,-84.505500,"
            ",,TOWER,1,"
            "00100,00700,R,5D,M,"
            "TEST,C,2026260\n"
        ),
        encoding="cp1252",
    )

    count = ObstacleDatabaseBuilder().build(
        source,
        database_path,
    )

    assert count == 1

    database = ObstacleDatabase(
        database_path,
        now_provider=lambda: (
            source.stat().st_mtime
        ),
    )

    provider = ObstacleRuntimeProvider(
        database
    )

    real_projector = (
        ObstacleProjectionComputer()
    )

    projection_calls = []

    class RecordingProjector:
        def project(
            self,
            **kwargs,
        ):
            result = real_projector.project(
                **kwargs
            )

            projection_calls.append(
                result
            )

            return result

    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=(
            tmp_path
            / "baro.json"
        ),
    )

    widget.timer.stop()
    qtbot.addWidget(widget)

    widget.resize(
        1024,
        600,
    )

    # Establish all normal runtime objects first.
    widget.update_data()

    assert widget.pfd is not None

    # Force the production full-render obstacle path
    # on regardless of the normal configuration file.
    widget.config.features.show_obstacles = True
    widget.config.features.show_synthetic_vision = True

    widget.guidance_touch_settings = replace(
        widget.guidance_touch_settings,
        synthetic_vision_enabled=True,
    )

    # Keep unrelated terrain graphics out of the
    # sampled obstacle-symbol area.
    widget.real_terrain_enabled = False

    widget.obstacles = provider
    widget.obstacle_projection_computer = (
        RecordingProjector()
    )

    # Deterministic ownship geometry near KHAO.
    widget.pfd.position_valid = True
    widget.pfd.latitude_deg = 39.3638
    widget.pfd.longitude_deg = -84.5400
    widget.pfd.indicated_alt_ft = 1500.0
    widget.pfd.heading_deg = 92.0
    widget.pfd.pitch_deg = 0.0
    widget.pfd.roll_deg = 0.0

    widget.sensor_watchdog_state = (
        widget.sensor_watchdog.evaluate(
            flight_data_available=True,
            position_valid=True,
            position_fresh=True,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=True,
        )
    )

    image = QImage(
        1024,
        600,
        QImage.Format.Format_ARGB32,
    )

    image.fill(0)

    painter = QPainter(
        image
    )

    try:
        widget.render(
            painter
        )

    finally:
        painter.end()

    assert image.isNull() is False

    # The complete PFD render must have reached the
    # real production obstacle projector.
    assert len(projection_calls) == 1

    projected = projection_calls[0]

    assert len(projected) == 1

    obstacle = projected[0]

    assert obstacle.ident == "39-FULL001"
    assert obstacle.threat is True

    # Verify that the actual rendered image contains
    # red obstacle-symbol pixels around the projected
    # threat location.
    center_x = int(
        round(
            obstacle.x_px
        )
    )

    center_y = int(
        round(
            obstacle.y_px
        )
    )

    red_pixel_found = False

    for y in range(
        max(
            0,
            center_y - 12,
        ),
        min(
            image.height(),
            center_y + 18,
        ),
    ):
        for x in range(
            max(
                0,
                center_x - 12,
            ),
            min(
                image.width(),
                center_x + 13,
            ),
        ):
            color = image.pixelColor(
                x,
                y,
            )

            if (
                color.red() >= 220
                and color.green() <= 60
                and color.blue() <= 60
            ):
                red_pixel_found = True
                break

        if red_pixel_found:
            break

    assert red_pixel_found is True

    widget.close()
