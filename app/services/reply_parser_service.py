import re
from typing import Dict, Optional


class ReplyParserService:
    """
    Parses distributor reply email text and extracts:

    - 30-day quantity
    - week1 quantity
    - week2 quantity
    - week3 quantity
    - week4 quantity

    Supported reply examples:

    1)
    30d_qty: 1000

    2)
    week1: 200
    week2: 250
    week3: 300
    week4: 250

    3)
    30d_qty: 1000
    week1: 200
    week2: 250
    week3: 300
    week4: 250
    """

    def execute(self, reply_text: str) -> Dict[str, Optional[int]]:
        if not reply_text or not reply_text.strip():
            return {
                "parsed_30d_qty": None,
                "parsed_week1_qty": None,
                "parsed_week2_qty": None,
                "parsed_week3_qty": None,
                "parsed_week4_qty": None,
                "parse_status": "FAILED",
            }

        cleaned_text = reply_text.strip().lower()

        parsed_30d_qty = self._extract_number(cleaned_text, r"30d_qty\s*:\s*(\d+)")
        parsed_week1_qty = self._extract_number(cleaned_text, r"week1\s*:\s*(\d+)")
        parsed_week2_qty = self._extract_number(cleaned_text, r"week2\s*:\s*(\d+)")
        parsed_week3_qty = self._extract_number(cleaned_text, r"week3\s*:\s*(\d+)")
        parsed_week4_qty = self._extract_number(cleaned_text, r"week4\s*:\s*(\d+)")

        parse_status = "PARSED" if any(
            value is not None
            for value in [
                parsed_30d_qty,
                parsed_week1_qty,
                parsed_week2_qty,
                parsed_week3_qty,
                parsed_week4_qty,
            ]
        ) else "FAILED"

        return {
            "parsed_30d_qty": parsed_30d_qty,
            "parsed_week1_qty": parsed_week1_qty,
            "parsed_week2_qty": parsed_week2_qty,
            "parsed_week3_qty": parsed_week3_qty,
            "parsed_week4_qty": parsed_week4_qty,
            "parse_status": parse_status,
        }

    @staticmethod
    def _extract_number(text: str, pattern: str) -> Optional[int]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None