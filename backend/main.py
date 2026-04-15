"""
合规质检 AI 双雄 - 后端服务
FastAPI 应用入口
"""
import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# 导入 Agent 模块
from agents.inspector import inspect_text, inspect_text_stream
from agents.advisor import chat, chat_stream
from tools.asr_tool import transcribe

app = FastAPI(
    title="合规质检 AI 双雄",
    description="催收合规质检 AI 系统，包含智能质检官和制度答疑官",
    version="1.0.0",
    docs_url="/api-docs",      # 避免与前端 /docs 路由冲突
    redoc_url="/api-redoc",
)

# CORS 配置（开发模式，允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ==================== 请求/响应模型 ====================

class TextInspectRequest(BaseModel):
    text: str


class AdvisorChatRequest(BaseModel):
    question: str
    history: Optional[List[Dict[str, str]]] = []


class DocCreateRequest(BaseModel):
    name: str
    content: str = ""


class DocUpdateRequest(BaseModel):
    content: str


# ==================== REST API ====================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "合规质检 AI 双雄"}


# --- 质检官 API ---

@app.post("/api/inspect/text")
async def inspect_text_api(request: TextInspectRequest):
    """文本质检接口"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    
    result = await inspect_text(request.text)
    return result


@app.post("/api/inspect/audio")
async def inspect_audio_api(file: UploadFile = File(...)):
    """音频质检接口（先 ASR 转文字，再质检）"""
    # 验证文件类型
    allowed_types = ["audio/mpeg", "audio/wav", "audio/wave", "audio/x-wav", "audio/mp3"]
    allowed_extensions = [".mp3", ".wav", ".m4a", ".ogg"]
    
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    
    if file_ext not in allowed_extensions and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式。支持：{', '.join(allowed_extensions)}"
        )
    
    # 读取音频数据
    audio_bytes = await file.read()
    
    # ASR 转文字
    transcript = transcribe(audio_bytes, file.filename)
    
    # 质检
    result = await inspect_text(transcript)
    result["asr_transcript"] = transcript
    
    return result


# --- 答疑官 API ---

@app.post("/api/advisor/chat")
async def advisor_chat_api(request: AdvisorChatRequest):
    """答疑官问答接口"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    response = await chat(request.question, request.history)
    return {"answer": response}


@app.post("/api/advisor/chat/stream")
async def advisor_chat_stream_api(request: AdvisorChatRequest):
    """答疑官流式问答接口（SSE）"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    return StreamingResponse(
        chat_stream(request.question, request.history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# --- 文档管理 API ---

@app.get("/api/docs")
async def get_docs():
    """获取文档列表"""
    docs = []
    for md_file in sorted(DATA_DIR.glob("*.md")):
        stat = md_file.stat()
        docs.append({
            "id": md_file.stem,
            "name": md_file.stem,
            "filename": md_file.name,
            "size": stat.st_size,
            "updated_at": stat.st_mtime
        })
    return {"docs": docs}


@app.post("/api/docs")
async def create_doc(request: DocCreateRequest):
    """创建新文档"""
    # 清理文件名，避免路径穿越
    safe_name = "".join(c for c in request.name if c.isalnum() or c in ("-", "_", " "))
    safe_name = safe_name.strip().replace(" ", "_")
    
    if not safe_name:
        raise HTTPException(status_code=400, detail="文档名称无效")
    
    doc_path = DATA_DIR / f"{safe_name}.md"
    
    if doc_path.exists():
        raise HTTPException(status_code=409, detail="文档已存在")
    
    doc_path.write_text(request.content, encoding="utf-8")
    
    return {
        "id": safe_name,
        "name": safe_name,
        "filename": f"{safe_name}.md",
        "message": "文档创建成功"
    }


@app.get("/api/docs/{doc_id}")
async def get_doc(doc_id: str):
    """获取文档内容"""
    # 安全检查
    safe_id = "".join(c for c in doc_id if c.isalnum() or c in ("-", "_"))
    doc_path = DATA_DIR / f"{safe_id}.md"
    
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="文档不存在")
    
    content = doc_path.read_text(encoding="utf-8")
    return {
        "id": safe_id,
        "name": safe_id,
        "content": content
    }


@app.put("/api/docs/{doc_id}")
async def update_doc(doc_id: str, request: DocUpdateRequest):
    """更新文档内容"""
    safe_id = "".join(c for c in doc_id if c.isalnum() or c in ("-", "_"))
    doc_path = DATA_DIR / f"{safe_id}.md"
    
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_path.write_text(request.content, encoding="utf-8")
    
    return {"id": safe_id, "message": "文档更新成功"}


@app.delete("/api/docs/{doc_id}")
async def delete_doc(doc_id: str):
    """删除文档"""
    safe_id = "".join(c for c in doc_id if c.isalnum() or c in ("-", "_"))
    doc_path = DATA_DIR / f"{safe_id}.md"
    
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_path.unlink()
    
    return {"message": "文档删除成功"}


# ==================== WebSocket ====================

@app.websocket("/ws/inspect")
async def ws_inspect(websocket: WebSocket):
    """质检流式 WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            # 接收文本数据
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            text = payload.get("text", "")
            if not text.strip():
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "文本内容不能为空"
                }))
                continue
            
            # 流式质检
            async for chunk in inspect_text_stream(text):
                # SSE 格式转 WebSocket 消息
                if chunk.startswith("data: "):
                    msg = chunk[6:].strip()
                    await websocket.send_text(msg)
                    await asyncio.sleep(0)  # 让出控制权
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            pass


@app.websocket("/ws/advisor")
async def ws_advisor(websocket: WebSocket):
    """答疑官流式 WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            question = payload.get("question", "")
            history = payload.get("history", [])
            
            if not question.strip():
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "问题不能为空"
                }))
                continue
            
            # 流式问答
            async for chunk in chat_stream(question, history):
                if chunk.startswith("data: "):
                    msg = chunk[6:].strip()
                    await websocket.send_text(msg)
                    await asyncio.sleep(0)
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            pass


# ==================== 静态文件服务 ====================

# 挂载前端构建产物（如果存在）
frontend_dist = Path(__file__).parent / "static"
if not frontend_dist.exists():
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    # 先挂载 assets 静态资源
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # SPA fallback：所有未匹配路由返回 index.html
    index_html = frontend_dist / "index.html"

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        ico = frontend_dist / "favicon.ico"
        if ico.exists():
            return FileResponse(str(ico))
        return JSONResponse({}, status_code=404)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """SPA fallback — 所有前端路由返回 index.html"""
        # 如果是真实文件则直接返回
        target = frontend_dist / full_path
        if target.exists() and target.is_file():
            return FileResponse(str(target))
        # 否则返回 SPA 入口
        return FileResponse(str(index_html))


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动合规质检 AI 双雄后端服务...")
    print(f"📋 文档目录: {DATA_DIR}")
    print(f"🤖 LLM Mock 模式: {os.getenv('LLM_MOCK', 'true')}")
    print(f"🎤 ASR Mock 模式: {os.getenv('ASR_MOCK', 'true')}")
    print("📡 API 文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
