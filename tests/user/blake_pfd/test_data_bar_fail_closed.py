from pathlib import Path

from pyefis.user.blake_pfd.pfd_demo import BlakePfdDemo


class TextCapturePainter:
    """Capture display text without retaining Qt painter objects."""

    def __init__(self) -> None:
        self.texts: list[str] = []

    def setBrush(self, *args) -> None:
        pass

    def setPen(self, *args) -> None:
        pass

    def setFont(self, *args) -> None:
        pass

    def drawRect(self, *args) -> None:
        pass

    def drawText(self, *args) -> None:
        self.texts.append(args[-1])


def test_top_bar_hides_stale_air_data_but_keeps_fresh_gps(
    qtbot,
    qapp,
    tmp_path: Path,
) -> None:
    widget = BlakePfdDemo(
        use_hardware=False,
        baro_state_path=tmp_path / "baro.json",
    )
    widget.timer.stop()
    qtbot.addWidget(widget)
    widget.update_data()

    assert widget.pfd is not None

    widget.config.features.show_tas = True
    widget.config.features.show_ground_speed = True
    widget.config.features.show_wind = True

    widget.sensor_watchdog_state = (
        widget.sensor_watchdog.evaluate(
            flight_data_available=True,
            position_valid=True,
            position_fresh=True,
            attitude_valid=True,
            attitude_fresh=True,
            air_data_valid=True,
            air_data_fresh=False,
        )
    )

    assert widget.sensor_watchdog_state.degraded is True

    painter = TextCapturePainter()
    widget.draw_top_data_bar(painter, widget.pfd, 1024)

    assert len(painter.texts) == 1
    displayed = painter.texts[0]

    # Air-data-dependent values must be explicitly unavailable.
    assert "TAS ---" in displayed
    assert "WIND ---" in displayed

    # Independent, fresh GPS ground speed must remain available.
    expected_gs = f"GS {widget.pfd.ground_speed_kt:.0f} KT"
    assert expected_gs in displayed

    # With fresh GPS but stale air data, preserve track
    # while suppressing altitude-dependent VNAV deviation.
    widget.config.features.show_vdi = True
    widget.config.vnav.enabled = True

    bottom_painter = TextCapturePainter()
    widget.draw_bottom_data_bar(
        bottom_painter,
        widget.pfd,
        1024,
        600,
    )

    assert len(bottom_painter.texts) == 1
    bottom_displayed = bottom_painter.texts[0]

    assert f"TRK {widget.pfd.track_deg:.0f}°" in bottom_displayed
    assert "VDI ---" in bottom_displayed

    # The separate VNAV box must not show a numeric
    # altitude error while air data is stale.
    vnav_painter = TextCapturePainter()
    widget.draw_vnav_info_box(
        vnav_painter,
        widget.pfd,
        1024,
        600,
    )

    assert "ALT ERR ---" in vnav_painter.texts
    assert (
        f"GP {widget.config.vnav.glidepath_angle_deg:.1f}°"
        in vnav_painter.texts
    )


    # GPS becomes stale while air data remains fresh.
    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=False,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )

    painter = TextCapturePainter()
    widget.draw_top_data_bar(painter, widget.pfd, 1024)
    displayed = painter.texts[0]

    assert f"TAS {widget.pfd.tas_kt:.0f} KT" in displayed
    assert "GS ---" in displayed
    assert "WIND ---" in displayed

    # The bottom bar must not present stale GPS-derived
    # navigation values as current readings.
    bottom_painter = TextCapturePainter()
    widget.draw_bottom_data_bar(
        bottom_painter,
        widget.pfd,
        1024,
        600,
    )

    assert len(bottom_painter.texts) == 1
    bottom_displayed = bottom_painter.texts[0]

    assert "TRK ---" in bottom_displayed
    assert "BRG ---" in bottom_displayed
    assert "DTK ---" in bottom_displayed
    assert "CDI ---" in bottom_displayed

    # Stale GPS must hide the position-derived VNAV target altitude.
    vnav_painter = TextCapturePainter()
    widget.draw_vnav_info_box(
        vnav_painter,
        widget.pfd,
        1024,
        600,
    )

    assert "TGT ALT ---" in vnav_painter.texts
    assert "ALT ERR ---" in vnav_painter.texts
    assert (
        f"GP {widget.config.vnav.glidepath_angle_deg:.1f}°"
        in vnav_painter.texts
    )


    # Stale GPS must hide waypoint and navigation-status readings.
    waypoint_painter = TextCapturePainter()
    widget.draw_waypoint_info_box(
        waypoint_painter, widget.pfd, 1024, 600
    )

    assert "BRG ---" in waypoint_painter.texts
    assert "DIS ---" in waypoint_painter.texts
    assert "CRS ERR ---" in waypoint_painter.texts

    navigation_painter = TextCapturePainter()
    widget.draw_navigation_status_box(
        navigation_painter, widget.pfd, 1024, 600
    )

    assert "DTK ---" in navigation_painter.texts
    assert "BRG ---" in navigation_painter.texts
    assert "DIS ---" in navigation_painter.texts

    # Fresh inputs restore all three readings.
    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=True,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )

    painter = TextCapturePainter()
    widget.draw_top_data_bar(painter, widget.pfd, 1024)
    displayed = painter.texts[0]

    assert f"TAS {widget.pfd.tas_kt:.0f} KT" in displayed
    assert f"GS {widget.pfd.ground_speed_kt:.0f} KT" in displayed
    assert (
        f"WIND {widget.pfd.wind_direction_deg:.0f}°/"
        f"{widget.pfd.wind_speed_kt:.0f} KT"
    ) in displayed


    # Fresh GPS must restore the bottom-bar navigation values.
    bottom_painter = TextCapturePainter()
    widget.draw_bottom_data_bar(
        bottom_painter,
        widget.pfd,
        1024,
        600,
    )

    assert len(bottom_painter.texts) == 1
    bottom_recovered = bottom_painter.texts[0]

    assert (
        f"VDI {widget.pfd.vdi:+.2f}°"
        in bottom_recovered
    )
    assert "VDI ---" not in bottom_recovered


    # Fresh GPS and air data must restore both VNAV values.
    vnav_painter = TextCapturePainter()
    widget.draw_vnav_info_box(
        vnav_painter, widget.pfd, 1024, 600
    )

    assert (
        f"TGT ALT {widget.pfd.glidepath_target_alt_ft:.0f}"
        in vnav_painter.texts
    )
    assert (
        f"ALT ERR {widget.pfd.glidepath_alt_error_ft:+.0f}"
        in vnav_painter.texts
    )

    assert (
        f"TRK {widget.pfd.track_deg:.0f}°"
        in bottom_recovered
    )
    assert "TRK ---" not in bottom_recovered
    assert "BRG ---" not in bottom_recovered
    assert "DTK ---" not in bottom_recovered
    assert "CDI ---" not in bottom_recovered

    # Fresh GPS must restore waypoint and navigation-status readings.
    waypoint_painter = TextCapturePainter()
    widget.draw_waypoint_info_box(
        waypoint_painter, widget.pfd, 1024, 600
    )

    assert (
        f"BRG {widget.pfd.bearing_deg:.0f}°"
        in waypoint_painter.texts
    )
    assert (
        f"DIS {widget.pfd.distance_to_waypoint_nm:.1f}NM"
        in waypoint_painter.texts
    )
    assert (
        f"CRS ERR {widget.pfd.course_error_deg:+.0f}°"
        in waypoint_painter.texts
    )

    navigation_painter = TextCapturePainter()
    widget.draw_navigation_status_box(
        navigation_painter, widget.pfd, 1024, 600
    )

    assert (
        f"DTK {widget.pfd.desired_track_deg:.0f}°"
        in navigation_painter.texts
    )
    assert (
        f"BRG {widget.pfd.bearing_deg:.0f}°"
        in navigation_painter.texts
    )
    assert (
        f"DIS {widget.pfd.distance_to_waypoint_nm:.1f} NM"
        in navigation_painter.texts
    )


    # Exercise the separate CDI/VDI instrument with
    # fresh GPS but stale air data.
    class IndicatorCapturePainter:
        def __init__(self) -> None:
            self.cdi_rectangles = 0
            self.vdi_polygons = 0

        def setPen(self, *args) -> None:
            pass

        def setBrush(self, *args) -> None:
            pass

        def drawLine(self, *args) -> None:
            pass

        def drawRect(self, *args) -> None:
            self.cdi_rectangles += 1

        def drawPolygon(self, *args) -> None:
            self.vdi_polygons += 1

    widget.config.features.show_cdi = True
    widget.config.features.show_vdi = True
    widget.config.vnav.enabled = True

    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=True,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=False,
    )

    indicator_painter = IndicatorCapturePainter()
    widget.draw_nav_cdi_vdi(
        indicator_painter,
        widget.pfd,
        1024,
        600,
    )

    # CDI depends on the still-fresh GPS position;
    # VDI must not draw using stale air data.
    assert indicator_painter.cdi_rectangles == 1
    assert indicator_painter.vdi_polygons == 0


    # Stale GPS must suppress both navigation indicators.
    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=False,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )

    indicator_painter = IndicatorCapturePainter()
    widget.draw_nav_cdi_vdi(
        indicator_painter,
        widget.pfd,
        1024,
        600,
    )

    assert indicator_painter.cdi_rectangles == 0
    assert indicator_painter.vdi_polygons == 0

    # Both indicators must return when GPS and air data are fresh.
    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=True,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )

    indicator_painter = IndicatorCapturePainter()
    widget.draw_nav_cdi_vdi(
        indicator_painter,
        widget.pfd,
        1024,
        600,
    )

    assert indicator_painter.cdi_rectangles == 1
    assert indicator_painter.vdi_polygons == 1


    # Direct-to must not display old guidance when GPS becomes stale.
    # Preserve an active guidance snapshot to exercise the renderer
    # independently of update_data(), which normally clears it.
    from dataclasses import replace

    widget.direct_to_guidance_state = replace(
        widget.direct_to_guidance_state,
        active=True,
        identifier="TEST",
        bearing_deg=135.0,
        distance_nm=12.5,
        course_error_deg=15.0,
    )

    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=False,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )

    dto_painter = TextCapturePainter()
    widget.draw_direct_to_guidance_box(
        dto_painter, 1024, 600
    )

    assert "DTO TEST" in dto_painter.texts
    assert "BRG ---   DIS ---" in dto_painter.texts
    assert "COURSE ---" in dto_painter.texts

    # Restoring GPS freshness must restore numeric guidance.
    widget.sensor_watchdog_state = widget.sensor_watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=True,
        attitude_valid=True,
        attitude_fresh=True,
        air_data_valid=True,
        air_data_fresh=True,
    )

    dto_painter = TextCapturePainter()
    widget.draw_direct_to_guidance_box(
        dto_painter, 1024, 600
    )

    assert "DTO TEST" in dto_painter.texts
    assert "BRG 135°   DIS 12.5 NM" in dto_painter.texts
    assert "RIGHT 15°" in dto_painter.texts

    widget.close()
    widget.deleteLater()
    qapp.processEvents()
