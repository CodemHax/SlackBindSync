from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from src.core.models import AdminRegister, AdminLogin, TokenCreate
from src.auth import auth_manager

router = APIRouter(prefix="/admin", tags=["admin"])

active_sessions = set()


async def verify_admin_session(x_admin_token: Optional[str] = Header(None)):
    if not x_admin_token or x_admin_token not in active_sessions:
        raise HTTPException(status_code=401, detail="Unauthorized - Admin login required")
    return x_admin_token


@router.post("/register")
async def register_admin(admin: AdminRegister):
    try:
        if await auth_manager.admin_exists():
            raise HTTPException(status_code=400, detail="Admin already registered")

        result = await auth_manager.register_admin(admin.username, admin.password)
        return {"message": "Admin registered successfully", "admin": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register admin: {str(e)}")


@router.post("/login")
async def login_admin(credentials: AdminLogin):
    try:
        if await auth_manager.authenticate_admin(credentials.username, credentials.password):
            session_token = auth_manager.generate_token()
            active_sessions.add(session_token)
            return {"message": "Login successful", "session_token": session_token}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/logout")
async def logout_admin(session_token: str = Depends(verify_admin_session)):
    active_sessions.discard(session_token)
    return {"message": "Logged out successfully"}


@router.get("/status")
async def admin_status():
    exists = await auth_manager.admin_exists()
    return {
        "admin_exists": exists,
        "registration_required": not exists
    }


@router.post("/tokens", dependencies=[Depends(verify_admin_session)])
async def create_token(token_data: TokenCreate):
    try:
        result = await auth_manager.create_api_token(
            name=token_data.name,
            description=token_data.description,
            expires_in_days=token_data.expires_in_days
        )
        return {
            "message": "Token created successfully",
            "token": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create token: {str(e)}")


@router.get("/tokens", dependencies=[Depends(verify_admin_session)])
async def list_tokens():
    try:
        tokens = await auth_manager.list_tokens()
        return {"tokens": tokens}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tokens: {str(e)}")


@router.patch("/tokens/{token_name}/revoke", dependencies=[Depends(verify_admin_session)])
async def revoke_token(token_name: str):
    try:
        success = await auth_manager.revoke_token(token_name)
        if success:
            return {"message": f"Token '{token_name}' revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="Token not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke token: {str(e)}")


@router.delete("/tokens/{token_name}", dependencies=[Depends(verify_admin_session)])
async def delete_token(token_name: str):
    try:
        success = await auth_manager.delete_token(token_name)
        if success:
            return {"message": f"Token '{token_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Token not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete token: {str(e)}")

