from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import memory, context

load_dotenv()

app = FastAPI(title="Memory Infrastructure")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory.router)
app.include_router(context.router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
