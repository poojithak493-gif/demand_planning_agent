import json
from pathlib import Path
from typing import List


class SKURepository:
    def __init__(self) -> None:
        self.file_path = Path("sample_data/skus.json")

    def get_all(self) -> List[dict]:
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)