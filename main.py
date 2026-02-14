# 最简FastAPI入口，只保留核心功能
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.agent import router as agent_route

# 创建FastAPI应用实例（Vercel会自动识别这个app变量）
app = FastAPI(title="极简FastAPI模板")

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有域名，生产环境需指定具体域名（如"http://localhost:8080"）
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=["*"],  # 允许所有请求方法（GET/POST/PUT/DELETE 等）
    allow_headers=["*"],  # 允许所有请求头
)


app.include_router(agent_route, prefix="/api")


# 根路径接口
@app.get("/")
async def root():
    return {"message": "Hello FastAPI on Vercel!", "status": "success"}

# ❗️重要：不要加uvicorn.run()，Vercel会自动处理运行逻辑
