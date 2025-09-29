# FastAPI Mock App
 
仅用于联调和演示，不是生产入口。  

- **生产服务**：请使用 Flask (`Backend/server.py`)  
- **Mock 服务启动**：  
  ```bash
  uvicorn playground.fastapi_mock_app.main:app --reload --port 8001
