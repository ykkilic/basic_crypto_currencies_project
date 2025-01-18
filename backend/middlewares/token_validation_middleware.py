from fastapi import Request, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from datetime import datetime, timezone
import time
from dotenv import load_dotenv
import os
import logging
from services.database import get_db
from models.models import Users, RolePermission, Pages

# .env dosyasından güvenlik anahtarını ve algoritmayı yükleyin
load_dotenv()

SECRET_KEY = os.getenv("SECURITY_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Hata loglama düzeyini belirleyin (özellikle geliştirme aşamasında debug kullanabilirsiniz)
logging.basicConfig(level=logging.DEBUG)

class TokenValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, excluded_paths: list[str]):
        super().__init__(app)
        self.excluded_paths = excluded_paths

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        try:
            db: Session = next(get_db())
            # Eğer istek excluded paths içinde değilse token doğrulaması yapılır
            if not any(request.url.path.startswith(path) for path in self.excluded_paths):
                # logging.debug("Token validation is required for this path.")

                # Authorization header'ını kontrol et
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.lower().startswith("bearer "):
                    raise HTTPException(
                        status_code=401,
                        detail="Access token required"
                    )
                
                token = auth_header.split(" ")[1]
                # print(token)
                self.verify_token(token)

                decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True})
                user_email = decoded_token.get("email")

                current_url = ("/"+request.headers.get("x-current-url").split("/")[-1])

                user = db.query(Users).filter(Users.email == user_email).first()

                check_page_exists = db.query(Pages).filter(Pages.page_path == current_url).first()

                if not user:
                    return JSONResponse(
                        status_code=401,
                        content={"error" : "user not found"}
                    )
                if not current_url:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Not Found Current URL Path", "status_code": 401}
                    )
                
                if not check_page_exists:
                    return JSONResponse(
                        status_code = 401,
                        content={"error" : "Not found current page"}
                    )
                
                check_permission = db.query(RolePermission).join(Pages).filter(Pages.page_path == current_url, RolePermission.role_id == user.role_id).all()
                if not check_permission:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail" : "You dont have permission"}
                    )
                
                
            else:
                logging.debug("Path is excluded from token validation.")

            # Bir sonraki middleware veya endpoint'e geç
            response = await call_next(request)
            return response

        except HTTPException as exc:
            # Hata durumunda JSON yanıt döndür
            logging.error(f"HTTPException: {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
        except Exception as e:
            # Beklenmedik bir hata durumunda genel bir yanıt döndür
            logging.error(f"Unexpected Error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error": str(e)},
            )

    def verify_token(self, token: str) -> None:
        try:
            # Token'ı doğrula
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True})

            # Exp kontrolü
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=401,
                    detail="Token does not have an expiration time"
                )
            
            # Current time ve exp zamanlarını karşılaştır
            current_time = time.time()  # time.time() kullanmak daha yaygın
            if current_time > exp:
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )

            # İsteğe bağlı olarak role veya user_id gibi ekstra doğrulamalar yapılabilir
            user_role = payload.get("role")
            if user_role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: Insufficient role"
                )

        except jwt.ExpiredSignatureError:
            logging.error("Token expired")
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            logging.error("Invalid token")
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

# class AuthMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         print("burda")
#         excluded_paths = [
#         ]
        
#         print(request.url)
#         if request.method == "OPTIONS":
#             return await call_next(request)
#         # Eğer istek 'excluded_paths' listesinde değilse, token kontrolü yapılacak
#         if request.url.path in excluded_paths:
#             return await call_next(request)

#         token = request.headers.get("Authorization")
#         current_url = str(request.url.path)  # URL'yi al

#         # Token ve current_url_path kontrolü
#         if not token:
#             return JSONResponse(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 content={"error": "Authorization token missing", "status_code": 401}
#             )
        
#         if not current_url:
#             return JSONResponse(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 content={"error": "Not Found Current URL Path", "status_code": 401}
#             )

#         # Token'ı Bearer token formatında çöz
#         token = token.split("Bearer ")[-1]
#         decoded_token = validate_token(token)

#         # Kullanıcı ID'sini al
#         user_id = decoded_token["user_id"]

        

#         # Veritabanı bağlantısı
#         db: Session = next(get_db())

#         # Kullanıcının bilgilerini User tablosundan al
#         user = db.query(Users).filter(Users.id == user_id).first()

#         if not user:
#             return JSONResponse(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 content={"error": "User not found", "status_code": 404}
#             )

#         # Kullanıcının rolüne göre sayfa izinlerini al
#         user_role_id = user.role_id  # Kullanıcının rolü, User tablosundan alındı
        
#         # Sayfa yolunun varlığını kontrol et
#         current_url = current_url.split("/")[1]
#         check_page_exists = db.query(Page).filter(Page.path == current_url).first()

#         if not check_page_exists:

#             return JSONResponse(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 content={"error": "Page not found in the system", "status_code": 404}
#             )

#         # Sayfa izinlerini kontrol et
#         user_permissions = db.query(RolePermission).join(Page).filter(Page.path == current_url, RolePermission.role_id == user_role_id).all()

#         if not user_permissions:
#             return JSONResponse(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 content={"error": "You do not have permission to access this page", "status_code": 403}
#             )


#         # Middleware'in geri kalanını çalıştır
#         request.state.user = user
#         response = await call_next(request)
#         return response