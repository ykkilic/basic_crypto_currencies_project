import sys
import os
import requests
import ssl
import pandas as pd
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, Table, MetaData, Float, TIMESTAMP
import traceback
import io

# Sistemin ana dizinini yol olarak ekleme
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Veritabanı yapılandırmalarını içe aktarma
from services.database import engine, db_host, db_name, db_password, db_port, db_username

class CryptoHistoryData:
    BASE_URL = "https://api.binance.com/api/v1/klines"

    def __init__(self, symbol="BTCUSDT", interval="1d", limit=1000):
        self.symbol = symbol
        self.interval = interval
        self.limit = limit

    def get_historical_data(self, start_time=None, end_time=None):
        params = {
            'symbol': self.symbol,
            'interval': self.interval,
            'limit': self.limit
        }

        context = ssl.create_default_context()
        context.set_ciphers('TLSv1.2')

        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

        try:
            response = requests.get(self.BASE_URL, params=params, verify=True, timeout=10)
            response.raise_for_status()  # HTTP hataları için istisna fırlat
            return response.json()  # JSON verisini döndür
        except requests.RequestException as e:
            print(f"API hatası: {e}")
            return None

    def format_data(self, raw_data):
        try:
            # Veriyi DataFrame formatında düzenleme
            df_pandas = pd.DataFrame({
                'open_time': [row[0] for row in raw_data],
                'open': [row[1] for row in raw_data],
                'high': [row[2] for row in raw_data],
                'low': [row[3] for row in raw_data],
                'close': [row[4] for row in raw_data],
                'volume': [row[5] for row in raw_data],
                'close_time': [row[6] for row in raw_data],
                'quote_asset_volume': [row[7] for row in raw_data],
                'number_of_trades': [row[8] for row in raw_data],
                'taker_buy_base_asset_volume': [row[9] for row in raw_data],
                'ignore': [row[11] for row in raw_data]  # 'taker_buy_quote_asset_volume' kaldırıldı
            })

            # Zaman dönüşümü
            df_pandas["open_time"] = pd.to_datetime(df_pandas["open_time"], unit="ms", errors="coerce")
            df_pandas["close_time"] = pd.to_datetime(df_pandas["close_time"], unit="ms", errors="coerce")

            # NaT ve NaN'ları temizle
            df_pandas = df_pandas.dropna(subset=["open_time", "close_time"])

            # Sayısal veri dönüşümü
            numeric_columns = [
                'open', 'high', 'low', 'close', 'volume',
                'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'ignore'
            ]
            for col in numeric_columns:
                df_pandas[col] = pd.to_numeric(df_pandas[col], errors='coerce')

            # Eksik sayısal verileri doldur veya kaldır
            df_pandas = df_pandas.dropna(subset=numeric_columns)

            return df_pandas
        except Exception as e:
            print(f"Veri formatlama hatası: {e}")
            traceback.print_exc()
            return pd.DataFrame()  # Boş DataFrame döndür

    def get_last_entry_time(self, table_name):
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_username,
                password=db_password,
                host=db_host,
                port=db_port
            )
            cursor = conn.cursor()
            query = sql.SQL("SELECT MAX(close_time) FROM {table}").format(table=sql.Identifier(table_name))
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Son giriş zamanını alırken hata: {e}")
            traceback.print_exc()
            return None

    def save_to_db(self, data, table_name, batch_size=100):
        try:
            if data.empty:
                print("Kaydedilecek veri yok.")
                return

            # Veritabanı tablosunun mevcut olup olmadığını kontrol et
            metadata = MetaData()
            metadata.reflect(bind=engine)
            if table_name not in metadata.tables:
                print(f"Tablo '{table_name}' veritabanında bulunamadı.")
                return

            # Insert işlemini batch'ler halinde gerçekleştir
            with engine.begin() as connection:
                for start in range(0, len(data), batch_size):
                    end = start + batch_size
                    batch = data.iloc[start:end]
                    batch.to_sql(
                        table_name, 
                        connection, 
                        index=False, 
                        if_exists='append', 
                        method='multi',
                        dtype={
                            'open_time': TIMESTAMP,
                            'close_time': TIMESTAMP,
                            'open': Float,
                            'high': Float,
                            'low': Float,
                            'close': Float,
                            'volume': Float,
                            'quote_asset_volume': Float,
                            'number_of_trades': Float,
                            'taker_buy_base_asset_volume': Float,
                            'ignore': Float
                        }
                    )
                    print(f"{table_name} tablosuna {start} ila {end} satır eklendi.")

            print("Tüm veriler başarıyla veritabanına kaydedildi.")
        except Exception as e:
            print(f"Veritabanına kaydetme hatası: {e}")
            traceback.print_exc()

    def save_to_db_copy(self, data, table_name):
        """
        PostgreSQL COPY komutunu kullanarak veriyi hızlıca veritabanına yükler.
        """
        try:
            if data.empty:
                print("Kaydedilecek veri yok.")
                return

            # DataFrame'i CSV formatına dönüştürün
            buffer = io.StringIO()
            data.to_csv(buffer, index=False, header=False)
            buffer.seek(0)

            # PostgreSQL'e bağlantı kurun
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_username,
                password=db_password,
                host=db_host,
                port=db_port
            )
            cursor = conn.cursor()

            # COPY komutunu kullanarak veriyi yükleyin
            cursor.copy_from(buffer, table_name, sep=",", null="", columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'ignore'
            ])
            conn.commit()

            cursor.close()
            conn.close()
            print("Veri başarıyla COPY komutuyla veritabanına yüklendi.")
        except Exception as e:
            print(f"COPY komutuyla veritabanına kaydetme hatası: {e}")
            traceback.print_exc()

    def get_data_and_update_db(self, table_name, use_copy=False):
        last_entry_time = self.get_last_entry_time(table_name)
        if last_entry_time:
            start_time = int(last_entry_time.timestamp() * 1000) + 1  # 1 ms ekleyerek çakışmayı önle
            print(f"Son giriş zamanı: {last_entry_time}. Yeni veriler {pd.to_datetime(start_time, unit='ms')} itibarıyla eklenecek.")
        else:
            start_time = None
            print("Veritabanında son giriş bulunamadı. İlk veri çekiliyor.")

        new_data = self.get_historical_data(start_time=start_time)

        if new_data:
            formatted_data = self.format_data(new_data)
            if not formatted_data.empty:
                if use_copy:
                    self.save_to_db_copy(formatted_data, table_name)
                else:
                    self.save_to_db(formatted_data, table_name)
            else:
                print("Formatlanmış veri boş.")
        else:
            print("Eklenecek yeni veri bulunamadı.")

# Kullanım
if __name__ == "__main__":
    # BTC verisi ekleme
    btc_data = CryptoHistoryData(symbol="BTCUSDT", interval="1d", limit=1000)
    btc_data.get_data_and_update_db("btc_data", use_copy=False)

    # ETH verisi ekleme
    eth_data = CryptoHistoryData(symbol="ETHUSDT", interval="1d", limit=1000)
    eth_data.get_data_and_update_db("eth_data", use_copy=False)

    cetus_data = CryptoHistoryData(symbol="CETUSUSDT", interval="1d", limit=1000)
    cetus_data.get_data_and_update_db("cetus_data", use_copy=False)

    crv_data = CryptoHistoryData(symbol="CRVUSDT", interval="1d", limit=1000)
    crv_data.get_data_and_update_db("crv_data", use_copy=False)

    kda_data = CryptoHistoryData(symbol="KDAUSDT", interval="1d", limit=1000)
    kda_data.get_data_and_update_db("kda_data", use_copy=False)
