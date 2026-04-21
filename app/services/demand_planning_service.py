class DemandPlanningService:
    def build_weekly_plan(
        self,
        distributor_code: str,
        parsed_lines: list[dict],
    ) -> dict:
        return {
            "distributor_code": distributor_code,
            "weekly_plan": [
                self._build_weekly_line(line)
                for line in parsed_lines
                if line.get("sku_code") and line.get("monthly_quantity") is not None
            ],
        }

    @staticmethod
    def _build_weekly_line(line: dict) -> dict:
        monthly_quantity = int(line["monthly_quantity"])
        base_quantity = monthly_quantity // 4
        remainder = monthly_quantity % 4

        weekly_quantities = [base_quantity] * 4
        for index in range(remainder):
            weekly_quantities[index] += 1

        return {
            "sku_code": line["sku_code"],
            "monthly_quantity": monthly_quantity,
            "week1_qty": weekly_quantities[0],
            "week2_qty": weekly_quantities[1],
            "week3_qty": weekly_quantities[2],
            "week4_qty": weekly_quantities[3],
        }
