from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SyntheticVisionObject:
    label: str
    rel_bearing_deg: float
    elevation_angle_deg: float
    distance_nm: float
    size: float = 1.0
    kind: str = "box"


@dataclass
class SyntheticVisionScene:
    sky_color: tuple[int, int, int] = (25, 95, 180)
    ground_color: tuple[int, int, int] = (105, 65, 25)
    objects: list[SyntheticVisionObject] | None = None


class SyntheticVisionComputer:
    def update(self, flight) -> SyntheticVisionScene:
        objects = []

        for index, distance_nm in enumerate([1, 2, 3, 4, 5], start=1):
            objects.append(
                SyntheticVisionObject(
                    label=f"HITS {index}",
                    rel_bearing_deg=self.angle_delta(
                        flight.desired_track_deg,
                        flight.heading_deg,
                    ),
                    elevation_angle_deg=-2.0,
                    distance_nm=float(distance_nm),
                    size=max(0.4, 1.2 - (distance_nm * 0.12)),
                    kind="hits",
                )
            )

        return SyntheticVisionScene(objects=objects)

    @staticmethod
    def angle_delta(new_angle: float, old_angle: float) -> float:
        return (new_angle - old_angle + 180.0) % 360.0 - 180.0


def project_object_to_screen(
    rel_bearing_deg: float,
    elevation_angle_deg: float,
    width: int,
    height: int,
    distance_nm: float = 1.0,
) -> tuple[int, int]:
    center_x = width // 2
    center_y = height // 2

    pixels_per_degree_x = width / 70.0
    pixels_per_degree_y = height / 45.0

    distance_scale = max(0.25, min(1.0, 1.0 / max(distance_nm, 0.5)))

    x = center_x + int(rel_bearing_deg * pixels_per_degree_x * distance_scale)
    y = center_y - int(elevation_angle_deg * pixels_per_degree_y * distance_scale)

    y -= int((1.0 - distance_scale) * 90)

    return x, y