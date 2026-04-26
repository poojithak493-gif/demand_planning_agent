```python id="4rwnnq"
import re
from typing import Dict, List, Tuple, Optional

from rapidfuzz import fuzz
from app.data.sku_data import load_sku_master_data


SKU_DATA = load_sku_master_data()


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.", "", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()


def get_sku_map() -> Dict[str, str]:
    sku_map = {}

    for row in SKU_DATA:
        sku_id = str(row.get("sku_id", "")).strip()
        sku_name = str(row.get("sku_name", "")).strip()

        if sku_name:
            sku_map[normalize_text(sku_name)] = sku_id

    return sku_map


def get_sku_id_to_name() -> Dict[str, str]:
    sku_names = {}

    for row in SKU_DATA:
        sku_id = str(row.get("sku_id", "")).strip()
        sku_name = str(row.get("sku_name", "")).strip()

        if sku_id:
            sku_names[sku_id] = sku_name

    return sku_names


def match_sku(
    text: str,
    min_score: int = 80
) -> Tuple[Optional[str], Optional[str], int]:

    if not text:
        return None, None, 0

    normalized_input = normalize_text(text)

    best_score = 0
    best_sku_id = None
    best_sku_name = None

    for row in SKU_DATA:
        sku_id = str(row.get("sku_id", "")).strip()
        sku_name = str(row.get("sku_name", "")).strip()

        normalized_name = normalize_text(sku_name)

        score = fuzz.ratio(normalized_input, normalized_name)

        if score > best_score:
            best_score = score
            best_sku_id = sku_id
            best_sku_name = sku_name

    if best_score >= min_score:
        return best_sku_id, best_sku_name, best_score

    return None, None, 0


def parse_reply(
    from_address: str,
    body: str
) -> List[Dict]:

    parsed_items = []

    lines = body.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        match = re.search(r"(.+?)\s*[-: ]\s*(\d+)", line)

        if not match:
            continue

        product_text = match.group(1).strip()
        quantity = int(match.group(2))

        sku_id, sku_name, score = match_sku(product_text)

        if not sku_id:
            continue

        parsed_items.append({
            "sku_id": sku_id,
            "sku_name": sku_name,
            "quantity": quantity,
            "matched_text": product_text,
            "match_score": score,
            "source": from_address
        })

    return parsed_items
```
