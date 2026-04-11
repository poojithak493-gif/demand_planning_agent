from app.repositories.distributor_repository import DistributorRepository
from app.services.validation_service import ValidationService


class DistributorService:
    def __init__(self) -> None:
        self.repository = DistributorRepository()

    def get_distributor_context(self, distributor_id: str) -> dict:
        distributor = self.repository.get_by_id(distributor_id)

        if not distributor:
            raise ValueError(f"Distributor '{distributor_id}' not found")

        return ValidationService.validate_distributor_context(distributor)