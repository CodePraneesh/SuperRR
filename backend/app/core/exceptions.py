"""
backend/app/core/exceptions.py
Custom exceptions and error response formatting for SupeRR Intelligence API.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class SupeRRException(Exception):
    """Base class for SupeRR Intelligence exceptions."""
    def __init__(self, message: str, status_code: int = 400, error_type: str = "BAD_REQUEST"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type


class PlayerNotFoundError(SupeRRException):
    """Raised when a player profile or split record is not found."""
    def __init__(self, player_name: str, scope: str = "", role: str = ""):
        scope_str = f" in {scope}" if scope else ""
        role_str = f" as {role}" if role else ""
        msg = f"Player '{player_name}' not found{scope_str}{role_str}."
        super().__init__(msg, status_code=404, error_type="PLAYER_NOT_FOUND")
        self.player_name = player_name
        self.scope = scope
        self.role = role


class InvalidScopeError(SupeRRException):
    """Raised when an invalid competition scope is requested."""
    def __init__(self, scope: str):
        msg = f"Invalid competition scope '{scope}'. Allowed scopes: 'IPL', 'T20I'."
        super().__init__(msg, status_code=422, error_type="INVALID_SCOPE")
        self.scope = scope


class InvalidRoleError(SupeRRException):
    """Raised when an invalid player role is requested."""
    def __init__(self, role: str):
        msg = f"Invalid role '{role}'. Allowed roles: 'Batter', 'Bowler'."
        super().__init__(msg, status_code=422, error_type="INVALID_ROLE")
        self.role = role


class ScoutingServiceError(SupeRRException):
    """Raised when an internal error occurs within the scouting engine."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_type="SCOUTING_SERVICE_ERROR")


# Helper validation functions for path/query parameters
def validate_scope(scope: str) -> str:
    s = scope.strip().upper()
    if s not in ("IPL", "T20I"):
        raise InvalidScopeError(scope)
    return s


def validate_role(role: str) -> str:
    r = role.strip().capitalize()
    if r not in ("Batter", "Bowler"):
        raise InvalidRoleError(role)
    return r


async def superr_exception_handler(request: Request, exc: SupeRRException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": exc.error_type,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=422,
        content={
            "detail": f"Validation Error: {msg}",
            "error_type": "VALIDATION_ERROR",
            "status_code": 422,
            "errors": errors
        }
    )
