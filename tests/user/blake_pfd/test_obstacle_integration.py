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
