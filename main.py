# 最简FastAPI入口，只保留核心功能
from fastapi import FastAPI
from routes.agent import router as agent_route

# 创建FastAPI应用实例（Vercel会自动识别这个app变量）
app = FastAPI(title="极简FastAPI模板")

app.include_router(agent_route, prefix="/api")


# 根路径接口
@app.get("/")
async def root():
    return {"message": "Hello FastAPI on Vercel!", "status": "success"}

# ❗️重要：不要加uvicorn.run()，Vercel会自动处理运行逻辑
