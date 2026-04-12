from app.repositories.distributor_repository import DistributorRepository


class DistributorService:
    def __init__(self) -> None:
        self.repository = DistributorRepository()

    def get_distributor_context(self, distributor_code: str) -> dict:
        distributor = self.repository.get_by_code(distributor_code)

        if not distributor:
            raise ValueError(f"Distributor '{distributor_code}' not found")

        distributor["distributor_id"] = str(distributor["distributor_id"])
        return distributor