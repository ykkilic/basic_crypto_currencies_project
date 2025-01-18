# backend/Dockerfile

# 1. Base Image
FROM python:3.11-slim

# 2. Çalışma Dizini Oluşturma
WORKDIR /app

# 3. Bağımlılıkları Yükleme
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 4. Uygulama Kodlarını Kopyalama
COPY . /app

# 5. Uygulamayı Başlatma
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
