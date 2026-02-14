# 最简FastAPI入口，只保留核心功能
from fastapi import FastAPI

# 创建FastAPI应用实例（Vercel会自动识别这个app变量）
app = FastAPI(title="极简FastAPI模板")

# 根路径接口
@app.get("/")
async def root():
    return {"message": "Hello FastAPI on Vercel!", "status": "success"}

# 测试API接口（示例）
@app.get("/api/hello/{name}")
async def hello(name: str):
    return {"greeting": f"Hello {name}!", "code": 200}

# ❗️重要：不要加uvicorn.run()，Vercel会自动处理运行逻辑