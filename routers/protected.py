from fastapi import APIRouter, Depends, HTTPException, Security
from utils import VerifyToken, get_token

router = APIRouter()
auth = VerifyToken()


@router.get("/api/public")
def public():
    """No access token required to access this route"""

    result = {
        "status": "success",
        "msg": (
            "Hello from a public endpoint! You don't need to be "
            "authenticated to see this."
        ),
    }
    return result


@router.get("/api/private")
def private(auth_result: str = Security(auth.verify)):
    """A valid access token is required to access this route"""
    return auth_result


# , dependencies=[Security(auth.verify, scopes=['write:author'])]
@router.get("/api/private-scoped")
def private_scoped(auth_result: str = Security(auth.verify, scopes=["write:author"])):
    """A valid access token and an appropriate scope are required to access
    this route
    """
    return auth_result
