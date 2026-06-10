import csv
from pathlib import Path

def test_csv_data_loader_default_data_directory():
    from pyefis.user.blake_pfd.data.csv_loader import CSVDataLoader

    loader = CSVDataLoader()
    assert loader.data_dir.name == "data"
    assert loader.data_dir.exists()


def test_load_csv_rows_from_temp_file(tmp_path: Path):
    from pyefis.user.blake_pfd.data import CSVDataLoader

    csv_path = tmp_path / "demo.csv"
    csv_path.write_text("name,altitude\nTower,1300\nRamp,300\n", encoding="utf-8")

    loader = CSVDataLoader(data_dir=tmp_path)
    rows = loader.load_rows("demo.csv")

    assert rows == [
        {"name": "Tower", "altitude": "1300"},
        {"name": "Ramp", "altitude": "300"},
    ]


def test_load_csv_data_with_absolute_path(tmp_path: Path):
    from pyefis.user.blake_pfd.data import load_csv_data

    csv_path = tmp_path / "absolute.csv"
    csv_path.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")

    rows = load_csv_data(csv_path)
    assert rows == [["x", "y"], ["1", "2"], ["3", "4"]]
