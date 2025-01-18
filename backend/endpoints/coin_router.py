from fastapi import APIRouter, Depends, Header, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from openpyxl import Workbook
from typing import List
import pandas as pd
import jwt
import json
import io
import re
import services.security
from services.database import get_db, Session, SessionLocal
from models.models import Users, BitcoinPrice, EthereumPrice, CurveCoinPrice, KadenaPrice, CetusPrice, Annotation
from schemas.s_annotation import AnnotationSchema
from schemas.s_crypto_enum import CurrencyEnum, TimeframeEnum, PriceResponse, currency_model_mapping
from utils.security_utils import OAuth2PasswordBearerWithCookies
from utils.utils import functions

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/prices", response_model=PriceResponse)
def get_prices(
    currency: CurrencyEnum = Query(..., description="Kripto para birimi"),
    timeframe: TimeframeEnum = Query(TimeframeEnum.all, description="Zaman dilimi"),
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(1000, ge=1, le=10000, description="Getirilecek kayıt sayısı"),
    db: Session = Depends(get_db)
):
    Model = currency_model_mapping.get(currency)
    if not Model:
        return JSONResponse(
            status_code=400,
            content={"detail" : "Geçersiz kripto birimi"}
        )
    
    try:
        query = db.query(Model)
        # print(query)
        if timeframe == TimeframeEnum.one_month:
            time_threshold = functions.last_month()
            query = query.filter(Model.close_time >= time_threshold)
        elif timeframe == TimeframeEnum.three_month:
            time_threshold = functions.last_three_month()
            print(f"time: {time_threshold}")
            query = query.filter(Model.close_time >= time_threshold)
            # print(query)
        elif timeframe == TimeframeEnum.one_year:
            time_threshold = functions.last_one_year()
            query = query.filter(Model.close_time >= time_threshold)

        prices = query.all() # .offset(skip).limit(limit)

        return PriceResponse(data=jsonable_encoder(prices))
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

@router.post("/save-annotation")
def get_me(annotation : AnnotationSchema, token : str = Depends(oauth2_scheme), db : Session = Depends(get_db)):
    print(annotation)
    try:
        user = functions.get_current_user(token, db)
        current_user = db.query(Users).filter(Users.email == user.email).first()

        new_annotation = Annotation(
            stock_symbol = annotation.stock_symbol,
            x_coord = annotation.x_coord,
            y_coord = annotation.y_coord,
            text = annotation.text,
            user_id = current_user.id
        )

        db.add(new_annotation)
        db.commit()
        db.refresh(new_annotation)

        return JSONResponse(
            status_code=200,
            content={"detail" : "Annotation saved successfully"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail" : "Internal Server Error"}
        )

@router.get("/get-annotation")
def get_annotation(token : str = Depends(oauth2_scheme), db : Session = Depends(get_db)):
    try:
        user = functions.get_current_user(token,db)
        current_user = db.query(Users).filter(Users.email == user.email).first()
        annotation = db.query(Annotation).filter(Annotation.user_id == current_user.id).all()
        return JSONResponse(
            status_code=200,
            content={"data" : jsonable_encoder(annotation)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail" : "Internal Server Error", "error" : str(e)}
        )

@router.get("/export-excel")
def export_excel(
    coinCurrency: CurrencyEnum,
    timeFrame: TimeframeEnum = TimeframeEnum.one_month,
    db: Session = Depends(get_db)
):
    try:
        # get_prices fonksiyonunu çağırıyoruz
        prices_response = functions.get_prices(
            export_type=coinCurrency,
            timeframe=timeFrame,
            db=db
        )
        # Hata durumunda get_prices fonksiyonu HTTPException fırlatır, bu yüzden burada kontrol etmeye gerek yok
        prices = prices_response.data
        
        # Güvenli dosya ismi oluşturma
        safe_coin_currency = re.sub(r'[^a-zA-Z0-9_\-]', '_', coinCurrency.value)
        filename = f"{safe_coin_currency}_data.xlsx"
        sheet_name = f"{safe_coin_currency}_data"
        print("içerde")

        # Excel dosyasını oluşturma
        excel_file = create_excel_with_summary(prices, sheet_name)
        print(excel_file)

        # Dosyayı StreamingResponse ile döndürme
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# @router.get("/export-excel")
# def export_excel(
#     coinCurrency: CurrencyEnum,
#     timeFrame: TimeframeEnum = TimeframeEnum.one_month,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # get_prices fonksiyonunu çağırıyoruz
#         prices_response = functions.get_prices(
#             export_type=coinCurrency,
#             timeframe=timeFrame,
#             db=db
#         )
        
#         # Hata durumunda get_prices fonksiyonu HTTPException fırlatır, bu yüzden burada kontrol etmeye gerek yok
#         prices = prices_response.data
        
#         # Güvenli dosya ismi oluşturma
#         safe_coin_currency = re.sub(r'[^a-zA-Z0-9_\-]', '_', coinCurrency.value)
#         filename = f"{safe_coin_currency}_data.xlsx"
#         sheet_name = f"{safe_coin_currency}_data"
        
#         # Excel dosyasını oluşturma
#         excel_file = create_excel(prices, sheet_name)

#         # Dosyayı StreamingResponse ile döndürme
#         return StreamingResponse(
#             excel_file,
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             headers={
#                 "Content-Disposition": f"attachment; filename={filename}"
#             }
#         )
#     except Exception as e:
#         print(e)
#         return JSONResponse(
#             status_code=500,
#             content={"detail" : "Internal Server Error"}
#         )

# @router.get("/export-excel")
# def export_excel(
#     coinCurrency: CurrencyEnum,
#     timeFrame: TimeframeEnum = TimeframeEnum.one_month,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # get_prices fonksiyonunu çağırıyoruz
#         prices_response = functions.get_prices(
#             export_type=coinCurrency,
#             timeframe=timeFrame,
#             db=db
#         )
        
#         # Hata durumunda get_prices fonksiyonu HTTPException fırlatır, bu yüzden burada kontrol etmeye gerek yok
#         prices = prices_response.data
#         filename = f"{coinCurrency}_data.xlsx"
#         sheet_name = f"{coinCurrency}_data"

#         excel_file = functions.create_excel(prices, sheet_name)

#         # Veriyi DataFrame'e dönüştürme
#         rows = [{
#             "id": str(p.id),
#             "open_time": str(p.open_time),
#             "open": str(p.open),
#             "high": str(p.high),
#             "low": str(p.low),
#             "close": str(p.close),
#             "volume": str(p.volume),
#             "close_time": str(p.close_time),
#             "quote_asset_volume": str(p.quote_asset_volume),
#             "number_of_trades": str(p.number_of_trades),
#             "taker_buy_base_asset_volume": str(p.taker_buy_base_asset_volume),
#             "ignore": str(p.ignore)
#         } for p in prices]

#         df = pd.DataFrame(rows)

#         # Excel dosyasını oluşturma
#         output = io.BytesIO()
#         with pd.ExcelWriter(output, engine="openpyxl") as writer:
#             df.to_excel(writer, index=False, sheet_name=sheet_name)
#         output.seek(0)  # Buffer'ın başına dön

#         # Dosyayı StreamingResponse ile döndürme
#         return StreamingResponse(
#             output,
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             headers={
#                 "Content-Disposition": f"attachment; filename={filename}"
#             }
#         )

#     except Exception as e:
#         print(e)
#         return JSONResponse(
#             status_code=500,
#             content={"detail" : str(e)}
#         )
