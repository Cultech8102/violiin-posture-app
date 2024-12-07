from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import cv2
import base64
import json
import numpy as np
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

app = FastAPI()

# CORSの設定
# 開発環境と本番環境の両方に対応
origins = os.getenv("CORS_ORIGINS", "").split(",")
if not origins:
    origins = ["http://localhost:3000"]  # デフォルト値

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            img_data = base64.b64decode(data.split(',')[1])
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 基本的な画像処理（エッジ検出など）
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            
            # 結果を送信
            _, buffer = cv2.imencode('.jpg', edges)
            img_str = base64.b64encode(buffer).decode('utf-8')
            await websocket.send_json({
                "image": f"data:image/jpeg;base64,{img_str}",
                "status": "processed"
            })
                
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}
        
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)