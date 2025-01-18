from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import jwt
import services.security
from services.database import get_db, Session, SessionLocal
from models.models import Users, Roles
from schemas.s_user import UserLoginSchema, Token, TokenData
from utils.security_utils import OAuth2PasswordBearerWithCookies

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: UserLoginSchema, db: Session = Depends(get_db)):
    try:
        user = db.query(Users).filter(Users.email == form_data.email, Users.password == form_data.password).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        user_role = db.query(Roles).filter(Roles.role_id == user.role_id).first()

        access_token_data = {"email" : user.email, "role" : user_role.role_name}
        access_token = services.security.create_access_token(access_token_data)

        refresh_token_data = {"email" : user.email, "role" : user_role.role_name}
        refresh_token = services.security.create_refresh_token(refresh_token_data)
        services.security.save_refresh_token_to_redis(refresh_token, user.username)

        response.set_cookie(key="refresh_token",
                            value=refresh_token,
                            httponly=True,
                            secure=True,
                            samesite="None",
                            max_age=3600,
                            path="/"
                            )
                            
        return JSONResponse(status_code=200, content={"access_token" : access_token, "token_type" : "bearer"})
    except Exception as e:
        print(str(e))
        return JSONResponse(status_code=500, content={
            "detail" : "Internal Server Error",
            "error" : f"{str(e)}"
        })

@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh Token Missing"
        )
    try:
        payload = jwt.decode(refresh_token, services.security.SECRET_KEY, algorithms=[services.security.ALGORITHM])
        email = payload.get("email")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid refresh token"
            )
        
        if not services.security.verify_refresh_token(refresh_token, email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid refresh token or token has expired"
            )
        
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid refresh token"
        )
    
    user_role = db.query(Roles).filter(Roles.role_id == user.role_id).first()
    access_token = {"email" : email, "role" : user_role}

    return {"access_token" : access_token, "token_type" : "bearer"}

oauth2_scheme = OAuth2PasswordBearerWithCookies(tokenUrl="/login/token")

print(oauth2_scheme)