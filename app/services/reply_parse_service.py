import re

from app.schemas.demand_schema import ParsedReplyResponse


class ReplyParseService:
    LINE_PATTERN = re.compile(
        r"^\s*(?P<sku_code>[A-Za-z0-9_-]+)\s*(?:[-:]\s*|\s+)(?P<monthly_quantity>\d+)\s*$"
    )

    def parse_reply(
        self,
        distributor_code: str,
        raw_reply_text: str | None = None,
        confirmed_by: str | None = None,
        notes: str | None = None,
    ) -> ParsedReplyResponse:
        if not raw_reply_text or not raw_reply_text.strip():
            raise ValueError("raw_reply_text must not be blank")

        parsed_lines = self._parse_raw_reply_text(raw_reply_text)
        normalized_notes = notes or "Parsed from raw distributor reply text."

        return ParsedReplyResponse(
            distributor_code=distributor_code,
            confirmed_by=confirmed_by,
            notes=normalized_notes,
            parsed_lines=parsed_lines,
        )

    def _parse_raw_reply_text(self, raw_reply_text: str) -> list[dict]:
        parsed_lines: list[dict] = []

        for raw_line in raw_reply_text.splitlines():
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue

            match = self.LINE_PATTERN.match(stripped_line)
            if not match:
                continue

            parsed_lines.append(
                self._normalize_line(
                    {
                        "sku_code": match.group("sku_code").upper(),
                        "sku_name": None,
                        "monthly_quantity": int(match.group("monthly_quantity")),
                        "raw_text": stripped_line,
                    }
                )
            )

        return parsed_lines
    @staticmethod
    def _normalize_line(line: dict) -> dict:
        return {
            "sku_code": line.get("sku_code", ""),
            "sku_name": line.get("sku_name"),
            "monthly_quantity": line.get("monthly_quantity"),
            "raw_text": line.get("raw_text"),
        }
