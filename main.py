from fastapi import FastAPI, Request
from pydantic import BaseModel
from rag_service import diagnose
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="FANUC Fault Doctor")


class DiagnoseRequest(BaseModel):
    error_code: str
    description: str | None = None


@app.post("/diagnose")
def diagnose_endpoint(req: DiagnoseRequest):
    result = diagnose(req.error_code, req.description)
    return result


@app.get("/health")
def health():
    return {"status": "ok"}

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    간단한 웹 UI 페이지 반환
    """
    return templates.TemplateResponse("index.html", {"request": request})