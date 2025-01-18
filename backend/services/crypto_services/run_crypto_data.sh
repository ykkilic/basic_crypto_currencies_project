#!/bin/bash

# Log dosyası için değişken tanımlayın
LOG_FILE="/home/cc_project/backend/logs/crypto_data_$(date +'%Y%m%d').log"

# Sanal ortamı etkinleştirin
source /home/cc_project/backend/venv/bin/activate

# Python betiğini çalıştırın ve çıktıyı log dosyasına yönlendirin
python3 /home/cc_project/backend/services/crypto_services/crypto_data.py >> "$LOG_FILE" 2>&1

# Sanal ortamı devre dışı bırakın
deactivate
