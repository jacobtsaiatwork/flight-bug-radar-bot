"""
根目錄啟動入口 (方便直接執行 uvicorn main:app 或 python main.py)
"""

import uvicorn
from app.main import app
from app.config import PORT

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
