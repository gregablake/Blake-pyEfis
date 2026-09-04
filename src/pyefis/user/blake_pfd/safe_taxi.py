from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyefis.user.blake_pfd.config_loader import (
    SafeTaxiConfig,
)
from pyefis.user.blake_pfd.database_importer import (
    distance_nm_between,
)


@dataclass
class TaxiMapState:
    active: bool = False

    airport_id: str = ""
    airport_name: str = ""

    airport_lat_deg: float | None = None
    airport_lon_deg: float | None = None
    airport_elevation_ft: float | None = None
    airport_distance_nm: float | None = None

    ownship_lat_deg: float | None = None
    ownship_lon_deg: float | None = None

    ownship_x: int = 0
    ownship_y: int = 0

    heading_deg: float = 0.0


class SafeTaxiComputer:
    """
    Conservative airport-surface eligibility computer.

    This class decides whether the Safe Taxi display may be
    presented. It does not itself claim that the aircraft is
    physically on a taxiway or runway.

    Activation requires:
      * valid and fresh aircraft position
      * finite navigation inputs
      * an airport within the configured radius
      * indicated altitude reasonably close to airport elevation
      * low IAS
      * low groundspeed
      * an external indication that the aircraft is not airborne

    Groundspeed hysteresis prevents display chatter around the
    activation threshold.

    If any required information is unavailable or malformed,
    Safe Taxi fails closed.
    """

    def __init__(
        self,
        database=None,
        config: SafeTaxiConfig | None = None,
    ) -> None:
        self.database = database
        self.config = (
            config
            if config is not None
            else SafeTaxiConfig()
        )

        self._validate_config()

        self.state = TaxiMapState()

        # Airport lookup can be expensive because the current
        # AviationDatabase implementation scans all airports.
        # Cache the result until the aircraft has moved a
        # meaningful distance.
        self._lookup_lat_deg: float | None = None
        self._lookup_lon_deg: float | None = None
        self._cached_nearest = None
        self._lookup_refresh_distance_nm = 0.10

    def _validate_config(self) -> None:
        values = (
            self.config.activate_groundspeed_kt,
            self.config.deactivate_groundspeed_kt,
            self.config.max_ias_kt,
            self.config.airport_search_radius_nm,
            self.config.max_airport_elevation_delta_ft,
        )

        if not all(
            isfinite(float(value))
            for value in values
        ):
            raise ValueError(
                "Safe Taxi configuration values must be finite"
            )

        if self.config.activate_groundspeed_kt < 0.0:
            raise ValueError(
                "Safe Taxi activation groundspeed "
                "must be nonnegative"
            )

        if (
            self.config.deactivate_groundspeed_kt
            <= self.config.activate_groundspeed_kt
        ):
            raise ValueError(
                "Safe Taxi deactivation groundspeed must be "
                "greater than activation groundspeed"
            )

        if self.config.max_ias_kt < 0.0:
            raise ValueError(
                "Safe Taxi maximum IAS must be nonnegative"
            )

        if self.config.airport_search_radius_nm <= 0.0:
            raise ValueError(
                "Safe Taxi airport search radius "
                "must be positive"
            )

        if (
            self.config.max_airport_elevation_delta_ft
            < 0.0
        ):
            raise ValueError(
                "Safe Taxi airport elevation delta "
                "must be nonnegative"
            )

    @staticmethod
    def _finite(value) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(result):
            return None

        return result

    def _inactive(
        self,
        *,
        heading_deg: float = 0.0,
    ) -> TaxiMapState:
        self.state = TaxiMapState(
            active=False,
            heading_deg=heading_deg,
        )
        return self.state

    def _nearest_airport(
        self,
        lat_deg: float,
        lon_deg: float,
    ):
        if self.database is None:
            return None

        refresh = (
            self._lookup_lat_deg is None
            or self._lookup_lon_deg is None
        )

        if not refresh:
            moved_nm = distance_nm_between(
                self._lookup_lat_deg,
                self._lookup_lon_deg,
                lat_deg,
                lon_deg,
            )

            refresh = (
                moved_nm
                >= self._lookup_refresh_distance_nm
            )

        if refresh:
            try:
                results = self.database.nearest_airports(
                    lat_deg,
                    lon_deg,
                    max_results=1,
                    include_closed=False,
                )
            except Exception:
                # Airport database problems must never cause
                # Safe Taxi to activate.
                self._cached_nearest = None
                self._lookup_lat_deg = None
                self._lookup_lon_deg = None
                return None

            self._lookup_lat_deg = lat_deg
            self._lookup_lon_deg = lon_deg

            self._cached_nearest = (
                results[0]
                if results
                else None
            )

        return self._cached_nearest

    def update(
        self,
        flight,
        *,
        position_fresh: bool = False,
        airborne: bool = True,
    ) -> TaxiMapState:
        heading_deg = self._finite(
            getattr(
                flight,
                "heading_deg",
                0.0,
            )
        )

        if heading_deg is None:
            heading_deg = 0.0

        if not bool(
            getattr(
                flight,
                "position_valid",
                False,
            )
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        if not position_fresh:
            return self._inactive(
                heading_deg=heading_deg,
            )

        if airborne:
            return self._inactive(
                heading_deg=heading_deg,
            )

        lat_deg = self._finite(
            getattr(
                flight,
                "latitude_deg",
                None,
            )
        )
        lon_deg = self._finite(
            getattr(
                flight,
                "longitude_deg",
                None,
            )
        )
        ground_speed_kt = self._finite(
            getattr(
                flight,
                "ground_speed_kt",
                None,
            )
        )
        ias_kt = self._finite(
            getattr(
                flight,
                "ias_kt",
                None,
            )
        )
        indicated_alt_ft = self._finite(
            getattr(
                flight,
                "indicated_alt_ft",
                None,
            )
        )

        if (
            lat_deg is None
            or lon_deg is None
            or ground_speed_kt is None
            or ias_kt is None
            or indicated_alt_ft is None
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        if not (
            -90.0 <= lat_deg <= 90.0
            and -180.0 <= lon_deg <= 180.0
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        if ground_speed_kt < 0.0 or ias_kt < 0.0:
            return self._inactive(
                heading_deg=heading_deg,
            )

        if ias_kt > self.config.max_ias_kt:
            return self._inactive(
                heading_deg=heading_deg,
            )

        if self.state.active:
            if (
                ground_speed_kt
                >= self.config.deactivate_groundspeed_kt
            ):
                return self._inactive(
                    heading_deg=heading_deg,
                )
        elif (
            ground_speed_kt
            > self.config.activate_groundspeed_kt
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        nearest = self._nearest_airport(
            lat_deg,
            lon_deg,
        )

        if nearest is None:
            return self._inactive(
                heading_deg=heading_deg,
            )

        try:
            distance_nm, airport = nearest
        except (TypeError, ValueError):
            return self._inactive(
                heading_deg=heading_deg,
            )

        distance_nm = self._finite(distance_nm)
        airport_elevation_ft = self._finite(
            getattr(
                airport,
                "elevation_ft",
                None,
            )
        )
        airport_lat_deg = self._finite(
            getattr(
                airport,
                "lat_deg",
                None,
            )
        )
        airport_lon_deg = self._finite(
            getattr(
                airport,
                "lon_deg",
                None,
            )
        )

        if (
            distance_nm is None
            or airport_elevation_ft is None
            or airport_lat_deg is None
            or airport_lon_deg is None
            or distance_nm < 0.0
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        if (
            distance_nm
            > self.config.airport_search_radius_nm
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        elevation_delta_ft = abs(
            indicated_alt_ft
            - airport_elevation_ft
        )

        if (
            elevation_delta_ft
            > self.config.max_airport_elevation_delta_ft
        ):
            return self._inactive(
                heading_deg=heading_deg,
            )

        airport_id = str(
            getattr(
                airport,
                "ident",
                "",
            )
        ).strip().upper()

        airport_name = str(
            getattr(
                airport,
                "name",
                "",
            )
        ).strip()

        if not airport_id:
            return self._inactive(
                heading_deg=heading_deg,
            )

        self.state = TaxiMapState(
            active=True,
            airport_id=airport_id,
            airport_name=airport_name,
            airport_lat_deg=airport_lat_deg,
            airport_lon_deg=airport_lon_deg,
            airport_elevation_ft=(
                airport_elevation_ft
            ),
            airport_distance_nm=distance_nm,
            ownship_lat_deg=lat_deg,
            ownship_lon_deg=lon_deg,
            heading_deg=heading_deg,
        )

        return self.state
