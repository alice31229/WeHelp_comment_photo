# 使用官方的 Python 鏡像
FROM python:3.9

# 設定工作目錄
WORKDIR /app

# 複製當前目錄中的所有文件到工作目錄中
COPY . .

# 安裝所需模組套件 -> --no-cache-dir 減少鏡像大小 避免快取記憶體導致模組版本依賴性問題
RUN pip install --no-cache-dir -r requirements.txt

# 開啟port
EXPOSE 8000

# 運行程式
CMD ["python", "app.py"]