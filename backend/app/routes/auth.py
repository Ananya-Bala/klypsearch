"""
routes/auth.py
--------------
HTTP layer for authentication.
Routes are thin: validate input (Pydantic), call the service, return the response.
All business logic lives in services/auth_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import LoginRequest, SignupRequest, TokenResponse, UserPublic
from app.services.auth_service import AuthError, login, signup

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (create or join an organization)",
)
def signup_route(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Two modes controlled by the request body:

    **Create organization** — provide `organization_name`:
    ```json
    { "name": "Ananya", "email": "ananya@example.com",
      "password": "password123", "organization_name": "Goldman Sachs" }
    ```

    **Join organization** — provide `invite_code`:
    ```json
    { "name": "Rahul", "email": "rahul@example.com",
      "password": "password123", "invite_code": "ABC12345" }
    ```
    """
    try:
        _, token = signup(db, payload)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
)
def login_route(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token = login(db, payload)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get the currently authenticated user",
)
def me_route(current_user: User = Depends(get_current_user)) -> User:
    """Protected route — requires `Authorization: Bearer <token>` header."""
    return current_user
