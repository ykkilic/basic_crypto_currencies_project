from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import jwt
import io
from datetime import datetime, timedelta
from typing import Union
import pandas as pd
from models.models import Users, BitcoinPrice, EthereumPrice
from services.security import SECRET_KEY, ALGORITHM
from services.database import get_db, Session
from schemas.s_crypto_enum import CurrencyEnum, TimeframeEnum, PriceResponse, currency_model_mapping, PriceModel

class functions():
    @staticmethod
    def get_current_user(token : str, db) -> Users:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("email")

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            user = db.query(Users).filter(Users.email == email).first()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            return user
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token, error : {str(e)}"
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail" : "Internal Server Error", "error" : str(e)}
            )

    @staticmethod
    def get_start_date(timeframe: TimeframeEnum) -> datetime:
        now = datetime.utcnow()
        if timeframe == TimeframeEnum.one_month:
            return now - timedelta(days=30)
        elif timeframe == TimeframeEnum.three_month:
            return now - timedelta(days=90)
        elif timeframe == TimeframeEnum.one_year:
            return now - timedelta(days=365)
        elif timeframe == TimeframeEnum.all:
            return datetime.min
        else:
            raise ValueError("Invalid Timeframe")

    @staticmethod
    def get_prices(
        export_type: CurrencyEnum,
        timeframe: TimeframeEnum,
        db: Session = Depends(get_db)
    ) -> Union[PriceResponse, JSONResponse]:
        model = currency_model_mapping.get(export_type)
        if not model:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Export Type"}
            )
        try:
            start_date = functions.get_start_date(timeframe)
            query=db.query(model)
            if timeframe != TimeframeEnum.all:
                query = query.filter(model.close_time >= start_date)
            
            data = query.all()
            data_response = [PriceModel.from_orm(item) for item in data]
            return PriceResponse(data=data_response)
        except ValueError as ve:
            return JSONResponse(
                status_code=400,
                content={"detail": str(ve)}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail" : str(e)}
            )

    def create_excel(prices, sheet_name):
        try:
            rows = [{
                "id": p.id,
                "open_time": p.open_time,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
                "close_time": p.close_time,
                "quote_asset_volume": p.quote_asset_volume,
                "number_of_trades": p.number_of_trades,
                "taker_buy_base_asset_volume": p.taker_buy_base_asset_volume,
                "ignore": p.ignore
            } for p in prices]

            df = pd.DataFrame(rows)

            numeric_columns = ['open', 'close', 'high', 'low']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            average_open = df['open'].mean()
            average_close = df['close'].mean()
            average_high = df['high'].mean()
            average_low = df['low'].mean()


            df['average_open'] = average_open
            df['average_close'] = average_close
            df['average_high'] = average_high
            df['average_low'] = average_low

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            output.seek(0)
            
            return output
        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=500,
                content={"detail" : "Internal Server Error"}
            )


    def last_month():
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        return one_month_ago
    
    def last_three_month():
        three_month_ago = datetime.utcnow() - timedelta(days=90)
        return three_month_ago

    def last_one_year():
        last_year = datetime.utcnow() - timedelta(days=365)
        return last_year