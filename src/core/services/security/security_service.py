"""Server-owned deny-by-default authorization foundation."""
from src.infrastructure.di.inject import inject
from src.infrastructure.security.token_validator import Principal


class PermissionDenied(RuntimeError):
    pass


@inject
class SecurityService:
    def authorize(self, principal: Principal | None, required_permission: str) -> None:
        if principal is None or not required_permission or required_permission not in principal.permissions:
            raise PermissionDenied("Permission denied")
