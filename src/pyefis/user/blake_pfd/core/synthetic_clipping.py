from __future__ import annotations

from math import isfinite

from pyefis.user.blake_pfd.core.synthetic_camera import (
    CameraPoint,
    ProjectedPoint,
)


def clip_camera_polygon_to_near_plane(
    points,
    *,
    near_plane_ft: float = 5.0,
) -> tuple[CameraPoint, ...]:
    try:
        near_plane = float(near_plane_ft)
        polygon = tuple(points)
    except (TypeError, ValueError):
        return ()

    if (
        not isfinite(near_plane)
        or near_plane <= 0.0
        or len(polygon) < 3
    ):
        return ()

    for point in polygon:
        if not _camera_point_valid(point):
            return ()

    if all(
        point.forward_ft >= near_plane
        for point in polygon
    ):
        return polygon

    clipped: list[CameraPoint] = []

    previous = polygon[-1]
    previous_inside = (
        previous.forward_ft
        >= near_plane
    )

    for current in polygon:
        current_inside = (
            current.forward_ft
            >= near_plane
        )

        if current_inside:
            if not previous_inside:
                intersection = (
                    _intersect_near_plane(
                        previous,
                        current,
                        near_plane,
                    )
                )

                if intersection is None:
                    return ()

                clipped.append(intersection)

            clipped.append(current)

        elif previous_inside:
            intersection = (
                _intersect_near_plane(
                    previous,
                    current,
                    near_plane,
                )
            )

            if intersection is None:
                return ()

            clipped.append(intersection)

        previous = current
        previous_inside = current_inside

    if len(clipped) < 3:
        return ()

    return tuple(clipped)


def clip_projected_polygon_to_screen(
    points,
    *,
    width_px: int,
    height_px: int,
) -> tuple[ProjectedPoint, ...]:
    try:
        width = float(width_px)
        height = float(height_px)
        polygon = tuple(points)
    except (TypeError, ValueError):
        return ()

    if (
        not isfinite(width)
        or not isfinite(height)
        or width <= 0.0
        or height <= 0.0
        or len(polygon) < 3
    ):
        return ()

    for point in polygon:
        if not _projected_point_valid(point):
            return ()

    if all(
        0.0 <= point.x_px <= width
        and 0.0 <= point.y_px <= height
        for point in polygon
    ):
        return polygon

    polygon = _clip_screen_boundary(
        polygon,
        inside=lambda point: (
            point.x_px >= 0.0
        ),
        intersect=lambda first, second: (
            _intersect_vertical(
                first,
                second,
                0.0,
            )
        ),
    )

    polygon = _clip_screen_boundary(
        polygon,
        inside=lambda point: (
            point.x_px <= width
        ),
        intersect=lambda first, second: (
            _intersect_vertical(
                first,
                second,
                width,
            )
        ),
    )

    polygon = _clip_screen_boundary(
        polygon,
        inside=lambda point: (
            point.y_px >= 0.0
        ),
        intersect=lambda first, second: (
            _intersect_horizontal(
                first,
                second,
                0.0,
            )
        ),
    )

    polygon = _clip_screen_boundary(
        polygon,
        inside=lambda point: (
            point.y_px <= height
        ),
        intersect=lambda first, second: (
            _intersect_horizontal(
                first,
                second,
                height,
            )
        ),
    )

    if len(polygon) < 3:
        return ()

    return tuple(
        ProjectedPoint(
            x_px=point.x_px,
            y_px=point.y_px,
            visible=True,
        )
        for point in polygon
    )


def _intersect_near_plane(
    first: CameraPoint,
    second: CameraPoint,
    near_plane_ft: float,
) -> CameraPoint | None:
    delta_forward = (
        second.forward_ft
        - first.forward_ft
    )

    if delta_forward == 0.0:
        return None

    fraction = (
        (
            near_plane_ft
            - first.forward_ft
        )
        / delta_forward
    )

    if not isfinite(fraction):
        return None

    right_ft = (
        first.right_ft
        + (
            second.right_ft
            - first.right_ft
        )
        * fraction
    )

    up_ft = (
        first.up_ft
        + (
            second.up_ft
            - first.up_ft
        )
        * fraction
    )

    if not (
        isfinite(right_ft)
        and isfinite(up_ft)
    ):
        return None

    return CameraPoint(
        right_ft=right_ft,
        up_ft=up_ft,
        forward_ft=near_plane_ft,
    )


def _clip_screen_boundary(
    points,
    *,
    inside,
    intersect,
) -> tuple[ProjectedPoint, ...]:
    polygon = tuple(points)

    if not polygon:
        return ()

    output: list[ProjectedPoint] = []

    previous = polygon[-1]
    previous_inside = inside(previous)

    for current in polygon:
        current_inside = inside(current)

        if current_inside:
            if not previous_inside:
                intersection = intersect(
                    previous,
                    current,
                )

                if intersection is None:
                    return ()

                output.append(intersection)

            output.append(current)

        elif previous_inside:
            intersection = intersect(
                previous,
                current,
            )

            if intersection is None:
                return ()

            output.append(intersection)

        previous = current
        previous_inside = current_inside

    return tuple(output)


def _intersect_vertical(
    first: ProjectedPoint,
    second: ProjectedPoint,
    x_px: float,
) -> ProjectedPoint | None:
    delta_x = (
        second.x_px
        - first.x_px
    )

    if delta_x == 0.0:
        return None

    fraction = (
        (x_px - first.x_px)
        / delta_x
    )

    y_px = (
        first.y_px
        + (
            second.y_px
            - first.y_px
        )
        * fraction
    )

    if not isfinite(y_px):
        return None

    return ProjectedPoint(
        x_px=x_px,
        y_px=y_px,
        visible=True,
    )


def _intersect_horizontal(
    first: ProjectedPoint,
    second: ProjectedPoint,
    y_px: float,
) -> ProjectedPoint | None:
    delta_y = (
        second.y_px
        - first.y_px
    )

    if delta_y == 0.0:
        return None

    fraction = (
        (y_px - first.y_px)
        / delta_y
    )

    x_px = (
        first.x_px
        + (
            second.x_px
            - first.x_px
        )
        * fraction
    )

    if not isfinite(x_px):
        return None

    return ProjectedPoint(
        x_px=x_px,
        y_px=y_px,
        visible=True,
    )


def _camera_point_valid(
    point,
) -> bool:
    return all(
        isfinite(value)
        for value in (
            point.right_ft,
            point.up_ft,
            point.forward_ft,
        )
    )


def _projected_point_valid(
    point,
) -> bool:
    return all(
        isfinite(value)
        for value in (
            point.x_px,
            point.y_px,
        )
    )
