import json
from pathlib import Path
from typing import Optional


class DistributorRepository:
    def __init__(self) -> None:
        self.file_path = Path("sample_data/distributors.json")

    def get_by_id(self, distributor_id: str) -> Optional[dict]:
        with open(self.file_path, "r", encoding="utf-8") as file:
            distributors = json.load(file)

        for distributor in distributors:
            if distributor["distributor_id"] == distributor_id:
                return distributor

        return None