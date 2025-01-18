# uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import endpoints.login_router
from services.database import engine, Base
from middlewares.token_validation_middleware import TokenValidationMiddleware
import endpoints.register_router
import endpoints.login_router
import endpoints.coin_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["http://localhost:3000",
           "http://127.0.0.1:3000",
           "http://46.31.77.149:3000",
           "https://localhost:3000",
           "https://127.0.0.1:3000",
           "https://46.31.77.149:3000"
           ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
    )

excluded_path = ["/register/save", 
                 "/login/token",
                 "/crypto/prices",
                 "/docs" 
                ]

app.add_middleware(TokenValidationMiddleware, excluded_paths=excluded_path)

app.include_router(endpoints.register_router.router, prefix="/register", tags=["register"])
app.include_router(endpoints.login_router.router, prefix="/login", tags=["login"])
app.include_router(endpoints.coin_router.router, prefix="/crypto", tags=["crypto"])


