# ⚖️ 催收合规 AI 双雄

> **智能质检官 × 制度答疑官** — 让合规管理进入 AI 时代

## 📋 项目简介

本系统基于 AI 大模型，为催收业务提供两大核心能力：

| 角色 | 功能 |
|------|------|
| 🔍 **智能质检官** | 接收通话文本/音频/短信，自动识别并标注违规句子，输出合规评分 |
| 📋 **制度答疑官** | 基于合规规则文档，实时回答催收人员的合规疑问 |

---

## 🏗 系统架构

```
compliance-ai/
├── backend/                    # Python 后端 (FastAPI)
│   ├── main.py                 # 应用入口 & API 路由
│   ├── agents/
│   │   ├── inspector.py        # 🔍 智能质检官 Agent
│   │   └── advisor.py          # 📋 制度答疑官 Agent
│   ├── tools/
│   │   └── asr_tool.py         # 🎙️ ASR 语音转文字工具
│   ├── data/
│   │   └── compliance_rules.md # 📄 质检规则文档（可在线编辑）
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Vue3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── Inspector.vue   # 质检官页面
│   │   │   ├── Advisor.vue     # 答疑官页面
│   │   │   └── DocManager.vue  # 文档管理页面
│   │   ├── api/index.ts        # API 封装
│   │   ├── App.vue             # 主布局
│   │   └── router/index.ts     # 路由配置
│   └── package.json
└── README.md
```

---

## 🚀 快速启动

### 1. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入 LLM API Key（或保持 LLM_MOCK=true 使用演示模式）
```

`.env` 配置说明：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_MOCK` | 演示模式（无需真实 API Key）| `true` |
| `LLM_API_KEY` | OpenAI 或兼容 API Key | - |
| `LLM_BASE_URL` | API 基础 URL | `https://api.openai.com/v1` |
| `LLM_MODEL` | 使用的模型名称 | `gpt-4o-mini` |
| `ASR_MOCK` | ASR 演示模式 | `true` |

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# 服务启动在 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 3. 启动前端（开发模式）

```bash
cd frontend
npm install --include=dev
node_modules/.bin/vite dev
# 前端启动在 http://localhost:5173
```

### 4. 或者使用前端构建产物（生产模式）

```bash
cd frontend
node_modules/.bin/vite build
# 构建产物在 dist/ 目录
# 后端会自动 serve 前端（访问 http://localhost:8000）
```

---

## 🎯 功能演示

### 🔍 质检官 - 文本质检

发送违规文本，系统会自动标注违规句子：

```bash
curl -X POST http://localhost:8000/api/inspect/text \
  -H "Content-Type: application/json" \
  -d '{"text": "你再不还钱我就让你坐牢！你这个骗子，我知道你家在哪里！"}'
```

**响应示例：**
```json
{
  "original_text": "你再不还钱我就让你坐牢！...",
  "violations": [
    {
      "sentence": "你再不还钱我就让你坐牢！",
      "rule": "1.1 威胁恐吓 - 法律威胁",
      "severity": "高",
      "explanation": "使用了非法律事实的法律威胁，属于严禁行为"
    }
  ],
  "score": 60,
  "summary": "【待改进】合规评分：60分。发现违规：高严重度 2 处"
}
```

### 🎙️ 质检官 - 音频质检

上传音频文件，自动 ASR 转录后质检：

```bash
curl -X POST http://localhost:8000/api/inspect/audio \
  -F "file=@your_audio.mp3"
```

### 📋 答疑官 - 合规问答

```bash
curl -X POST http://localhost:8000/api/advisor/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "催收时可以在晚上几点打电话？", "history": []}'
```

### 📄 文档管理

```bash
# 获取文档列表
curl http://localhost:8000/api/docs

# 获取文档内容
curl http://localhost:8000/api/docs/compliance_rules

# 更新文档
curl -X PUT http://localhost:8000/api/docs/compliance_rules \
  -H "Content-Type: application/json" \
  -d '{"content": "# 新的规则内容..."}'
```

---

## 🤖 Agent 架构说明

### 质检官 Agent (`agents/inspector.py`)

```
用户输入（文本/音频）
    │
    ▼
[Tool: load_compliance_rules]  ← 加载本地规则文档
    │
    ▼
[Tool: asr_transcribe]         ← 音频转文字（如果是音频）
    │
    ▼
[Tool: label_violations]       ← 基于 LLM 打标违规句子
    │
    ▼
结构化质检报告 + 合规评分
```

### 答疑官 Agent (`agents/advisor.py`)

```
用户问题
    │
    ▼
[Tool: search_compliance_docs]  ← 关键词检索相关段落（RAG）
    │
    ▼
[LLM] 结合检索结果生成回答
    │
    ▼
流式输出（打字机效果）
```

---

## 📡 API 接口文档

启动后访问 http://localhost:8000/docs 查看完整 Swagger API 文档。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/inspect/text` | 文本质检 |
| POST | `/api/inspect/audio` | 音频质检 |
| POST | `/api/advisor/chat` | 答疑官问答 |
| POST | `/api/advisor/chat/stream` | 答疑官流式问答 (SSE) |
| GET | `/api/docs` | 获取文档列表 |
| POST | `/api/docs` | 创建文档 |
| GET | `/api/docs/{id}` | 获取文档内容 |
| PUT | `/api/docs/{id}` | 更新文档 |
| DELETE | `/api/docs/{id}` | 删除文档 |
| WS | `/ws/inspect` | 质检流式 WebSocket |
| WS | `/ws/advisor` | 答疑流式 WebSocket |

---

## 🔧 接入真实 LLM

将 `.env` 中的 `LLM_MOCK=true` 改为 `LLM_MOCK=false`，并填入：

```env
LLM_MOCK=false
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

支持任何 OpenAI 兼容的 API（如 Azure OpenAI、本地 Ollama 等）。

---

## 🎙️ 接入真实 ASR

将 `ASR_MOCK=false`，系统会尝试使用 `openai-whisper`：

```bash
pip install openai-whisper
```

或修改 `tools/asr_tool.py` 接入其他 ASR 服务。

---

*Built with ❤️ | 催收合规 AI 双雄 v1.0*
