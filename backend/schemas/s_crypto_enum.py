from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import List

from models.models import BitcoinPrice, EthereumPrice, CurveCoinPrice, KadenaPrice, CetusPrice


class CurrencyEnum(str, Enum):
    btc = "btc"
    eth = "eth"
    crv = "crv"
    kda = "kda"
    cetus = "cetus"

class TimeframeEnum(str, Enum):
    all = "all"
    one_month = "one-month"
    three_month = "three-month"
    one_year = "one-year"

currency_model_mapping = {
    CurrencyEnum.btc: BitcoinPrice,
    CurrencyEnum.eth: EthereumPrice,
    CurrencyEnum.crv: CurveCoinPrice,
    CurrencyEnum.kda: KadenaPrice,
    CurrencyEnum.cetus: CetusPrice
}

class PriceModel(BaseModel):
    id: int
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime
    quote_asset_volume: float
    number_of_trades: float
    taker_buy_base_asset_volume: float
    ignore: float

    class Config:
        orm_mode = True
        from_attributes = True

# Response model bu olacak
class PriceResponse(BaseModel):
    data: List[PriceModel]



