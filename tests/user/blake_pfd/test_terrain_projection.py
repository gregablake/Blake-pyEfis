from __future__ import annotations

from pyefis.user.blake_pfd.core.terrain_projection import (
    TerrainProjectionComputer,
)
from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
    TerrainSurfaceVertex,
    TerrainTriangle,
)


def simple_surface() -> TerrainSurface:
    return TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=0.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )


def test_visible_terrain_triangle_projects() -> None:
    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 1
    assert projected.triangles[0].visible is True


def test_projected_triangle_preserves_elevations() -> None:
    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    triangle = projected.triangles[0]

    assert triangle.elevations_ft == (
        1000.0,
        1000.0,
        1300.0,
    )


def test_pitch_up_moves_terrain_down() -> None:
    computer = TerrainProjectionComputer()

    level = computer.project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    nose_up = computer.project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=10.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert (
        nose_up.triangles[0].first.y_px
        > level.triangles[0].first.y_px
    )


def test_triangle_behind_aircraft_is_hidden() -> None:
    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=180.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert projected.triangles[0].visible is False


def test_invalid_surface_fails_closed() -> None:
    projected = TerrainProjectionComputer().project(
        surface=TerrainSurface(
            valid=False,
            message="TERRAIN SAMPLE UNAVAILABLE",
        ),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is False
    assert projected.triangles == ()
    assert projected.message == (
        "TERRAIN SURFACE INVALID"
    )


def test_bad_triangle_index_fails_closed() -> None:
    surface = TerrainSurface(
        vertices=simple_surface().vertices,
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=99,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    projected = TerrainProjectionComputer().project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is False
    assert projected.triangles == ()
    assert projected.message == (
        "TERRAIN TRIANGLE INVALID"
    )


def test_partially_offscreen_triangle_is_clipped_visible() -> None:
    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-5000.0,
                up_ft=-300.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=0.0,
                up_ft=-300.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=5000.0,
                east_ft=500.0,
                up_ft=-300.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    projected = TerrainProjectionComputer().project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    triangle = projected.triangles[0]

    assert triangle.visible is True
    assert len(triangle.points) >= 3

    for point in triangle.points:
        assert point.visible is True
        assert 0.0 <= point.x_px <= 1280.0
        assert 0.0 <= point.y_px <= 720.0


def test_near_plane_crossing_triangle_is_clipped_visible() -> None:
    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=0.0,
                east_ft=0.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=100.0,
                east_ft=-10.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=100.0,
                east_ft=10.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    projected = TerrainProjectionComputer().project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    triangle = projected.triangles[0]

    assert triangle.visible is True
    assert len(triangle.points) >= 3

    for point in triangle.points:
        assert point.visible is True
        assert 0.0 <= point.x_px <= 1280.0
        assert 0.0 <= point.y_px <= 720.0


def test_partial_surface_projects_without_invalid_indices() -> None:
    from pyefis.user.blake_pfd.core.terrain_surface import (
        TerrainSurfaceGenerator,
    )

    sample_count = 0

    def sampler(
        latitude,
        longitude,
    ):
        nonlocal sample_count

        sample_count += 1

        if sample_count == 1:
            return None

        return 1000.0

    surface = TerrainSurfaceGenerator(
        elevation_sampler=sampler,
        forward_distances_nm=(
            1.0,
            2.0,
            3.0,
        ),
        lateral_fractions=(
            -1.0,
            0.0,
            1.0,
        ),
        half_width_ratio=0.5,
    ).generate(
        aircraft_lat_deg=39.0,
        aircraft_lon_deg=-84.0,
        aircraft_alt_ft=1500.0,
        heading_deg=0.0,
    )

    assert surface.valid is True
    assert surface.message == "TERRAIN PARTIAL"
    assert len(surface.vertices) == 8
    assert len(surface.triangles) == 6

    for triangle in surface.triangles:
        assert (
            triangle.first_index
            < len(surface.vertices)
        )
        assert (
            triangle.second_index
            < len(surface.vertices)
        )
        assert (
            triangle.third_index
            < len(surface.vertices)
        )


def test_shared_vertices_are_transformed_once_per_projection() -> None:
    from pyefis.user.blake_pfd.core.synthetic_camera import (
        SyntheticCamera,
    )

    class CountingCamera(SyntheticCamera):
        def __init__(self) -> None:
            super().__init__()
            self.prepared_transform_calls = 0

        def world_to_camera_prepared(
            self,
            *,
            north_ft,
            east_ft,
            up_ft,
            orientation,
        ):
            self.prepared_transform_calls += 1

            return super().world_to_camera_prepared(
                north_ft=north_ft,
                east_ft=east_ft,
                up_ft=up_ft,
                orientation=orientation,
            )

    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=-500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=2,
                third_index=3,
            ),
            TerrainTriangle(
                first_index=0,
                second_index=3,
                third_index=1,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    camera = CountingCamera()

    projected = TerrainProjectionComputer(
        camera=camera,
    ).project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 2

    # Four unique terrain vertices should require
    # exactly four prepared camera transforms.
    assert camera.prepared_transform_calls == 4


def test_shared_vertices_are_projected_once_per_projection() -> None:
    from pyefis.user.blake_pfd.core.synthetic_camera import (
        SyntheticCamera,
    )

    class CountingCamera(SyntheticCamera):
        def __init__(self) -> None:
            super().__init__()
            self.prepared_project_calls = 0

        def project_prepared(
            self,
            point,
            *,
            projection,
        ):
            self.prepared_project_calls += 1

            return super().project_prepared(
                point,
                projection=projection,
            )

    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=-500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=2,
                third_index=3,
            ),
            TerrainTriangle(
                first_index=0,
                second_index=3,
                third_index=1,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    camera = CountingCamera()

    projected = TerrainProjectionComputer(
        camera=camera,
    ).project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 2

    # The two triangles share vertices 0 and 3.
    # Four unique source vertices should therefore
    # require only four prepared camera projections.
    assert camera.prepared_project_calls == 4


def test_fully_front_triangle_skips_near_plane_clipper(
    monkeypatch,
) -> None:
    import pyefis.user.blake_pfd.core.terrain_projection as terrain_projection_module

    clip_calls = 0

    original_clipper = (
        terrain_projection_module
        .clip_camera_polygon_to_near_plane
    )

    def counting_clipper(
        points,
        *,
        near_plane_ft=5.0,
    ):
        nonlocal clip_calls
        clip_calls += 1

        return original_clipper(
            points,
            near_plane_ft=near_plane_ft,
        )

    monkeypatch.setattr(
        terrain_projection_module,
        "clip_camera_polygon_to_near_plane",
        counting_clipper,
    )

    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 1
    assert projected.triangles[0].visible is True

    # All three source vertices are already safely
    # forward of the near plane, so generic polygon
    # clipping should not be needed.
    assert clip_calls == 0


def test_fully_onscreen_triangle_skips_screen_clipper(
    monkeypatch,
) -> None:
    import pyefis.user.blake_pfd.core.terrain_projection as terrain_projection_module

    clip_calls = 0

    original_clipper = (
        terrain_projection_module
        .clip_projected_polygon_to_screen
    )

    def counting_clipper(
        points,
        *,
        width_px,
        height_px,
    ):
        nonlocal clip_calls
        clip_calls += 1

        return original_clipper(
            points,
            width_px=width_px,
            height_px=height_px,
        )

    monkeypatch.setattr(
        terrain_projection_module,
        "clip_projected_polygon_to_screen",
        counting_clipper,
    )

    projected = TerrainProjectionComputer().project(
        surface=simple_surface(),
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 1
    assert projected.triangles[0].visible is True

    # Every projected source vertex is already
    # inside the screen, so generic screen polygon
    # clipping should not be needed.
    assert clip_calls == 0


def test_partially_offscreen_triangle_uses_screen_clipper(
    monkeypatch,
) -> None:
    import pyefis.user.blake_pfd.core.terrain_projection as terrain_projection_module

    clip_calls = 0

    original_clipper = (
        terrain_projection_module
        .clip_projected_polygon_to_screen
    )

    def counting_clipper(
        points,
        *,
        width_px,
        height_px,
    ):
        nonlocal clip_calls
        clip_calls += 1

        return original_clipper(
            points,
            width_px=width_px,
            height_px=height_px,
        )

    monkeypatch.setattr(
        terrain_projection_module,
        "clip_projected_polygon_to_screen",
        counting_clipper,
    )

    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-5000.0,
                up_ft=-300.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=0.0,
                up_ft=-300.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=5000.0,
                east_ft=500.0,
                up_ft=-300.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    projected = TerrainProjectionComputer().project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert projected.triangles[0].visible is True

    # At least one source vertex is outside the
    # screen, so polygon clipping must still run.
    assert clip_calls == 1


def test_camera_orientation_is_prepared_once_per_projection() -> None:
    from pyefis.user.blake_pfd.core.synthetic_camera import (
        SyntheticCamera,
    )

    class CountingCamera(SyntheticCamera):
        def __init__(self) -> None:
            super().__init__()
            self.prepare_orientation_calls = 0
            self.prepared_transform_calls = 0

        def prepare_orientation(
            self,
            *,
            heading_deg,
            pitch_deg,
            roll_deg,
        ):
            self.prepare_orientation_calls += 1

            return super().prepare_orientation(
                heading_deg=heading_deg,
                pitch_deg=pitch_deg,
                roll_deg=roll_deg,
            )

        def world_to_camera_prepared(
            self,
            *,
            north_ft,
            east_ft,
            up_ft,
            orientation,
        ):
            self.prepared_transform_calls += 1

            return super().world_to_camera_prepared(
                north_ft=north_ft,
                east_ft=east_ft,
                up_ft=up_ft,
                orientation=orientation,
            )

    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=-500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=2,
                third_index=3,
            ),
            TerrainTriangle(
                first_index=0,
                second_index=3,
                third_index=1,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    camera = CountingCamera()

    projected = TerrainProjectionComputer(
        camera=camera,
    ).project(
        surface=surface,
        heading_deg=37.0,
        pitch_deg=8.0,
        roll_deg=-12.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 2

    assert camera.prepare_orientation_calls == 1
    assert camera.prepared_transform_calls == 4


def test_camera_projection_is_prepared_once_per_projection() -> None:
    from pyefis.user.blake_pfd.core.synthetic_camera import (
        SyntheticCamera,
    )

    class CountingCamera(SyntheticCamera):
        def __init__(self) -> None:
            super().__init__()
            self.prepare_projection_calls = 0
            self.prepared_project_calls = 0

        def prepare_projection(
            self,
            *,
            width_px,
            height_px,
            horizontal_fov_deg=70.0,
            vertical_fov_deg=45.0,
            near_plane_ft=5.0,
        ):
            self.prepare_projection_calls += 1

            return super().prepare_projection(
                width_px=width_px,
                height_px=height_px,
                horizontal_fov_deg=horizontal_fov_deg,
                vertical_fov_deg=vertical_fov_deg,
                near_plane_ft=near_plane_ft,
            )

        def project_prepared(
            self,
            point,
            *,
            projection,
        ):
            self.prepared_project_calls += 1

            return super().project_prepared(
                point,
                projection=projection,
            )

    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=-500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=3000.0,
                east_ft=500.0,
                up_ft=-500.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1000.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=-500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6000.0,
                east_ft=500.0,
                up_ft=-200.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=1300.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=2,
                third_index=3,
            ),
            TerrainTriangle(
                first_index=0,
                second_index=3,
                third_index=1,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    camera = CountingCamera()

    projected = TerrainProjectionComputer(
        camera=camera,
    ).project(
        surface=surface,
        heading_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        width_px=1280,
        height_px=720,
    )

    assert projected.valid is True
    assert len(projected.triangles) == 2

    assert camera.prepare_projection_calls == 1
    assert camera.prepared_project_calls == 4
