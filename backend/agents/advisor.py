"""
制度答疑官 Agent
负责回答催收合规相关问题，基于本地文档提供准确答案
"""
import os
import json
import re
from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"


def load_all_documents() -> Dict[str, str]:
    """加载 data 目录下所有 Markdown 文档"""
    docs = {}
    for md_file in DATA_DIR.glob("*.md"):
        docs[md_file.name] = md_file.read_text(encoding="utf-8")
    return docs


def search_relevant_passages(query: str, docs: Dict[str, str], max_passages: int = 5) -> List[str]:
    """
    关键词搜索相关段落
    """
    # 提取查询关键词（简单分词）
    keywords = _extract_keywords(query)
    
    passages = []
    
    for doc_name, content in docs.items():
        lines = content.split("\n")
        
        # 按段落分割（以 ## 或 ### 开头的行作为段落分隔）
        current_section = []
        current_title = doc_name
        
        for line in lines:
            if line.startswith("##"):
                # 保存上一个段落
                if current_section:
                    section_text = "\n".join(current_section)
                    score = _score_passage(section_text, keywords)
                    if score > 0:
                        passages.append((score, f"[{current_title}]\n{section_text}"))
                current_title = line.strip("# ").strip()
                current_section = [line]
            else:
                current_section.append(line)
        
        # 保存最后一个段落
        if current_section:
            section_text = "\n".join(current_section)
            score = _score_passage(section_text, keywords)
            if score > 0:
                passages.append((score, f"[{current_title}]\n{section_text}"))
    
    # 按分数排序，取前 N 个
    passages.sort(key=lambda x: x[0], reverse=True)
    return [p[1] for p in passages[:max_passages]]


def _extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词（支持中文子串检索）"""
    # 移除标点符号，按常见分隔符分词
    words = re.split(r'[，。？！、\s]+', text)
    # 过滤短词和停用词
    stop_words = {"的", "了", "吗", "呢", "啊", "是", "有", "在", "和", "与", "或", "我", "你", "他", "她", "可以", "怎么", "什么", "如何", "几点", "时候"}
    keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
    
    # 额外提取单个重要汉字组合（滑窗2-4字）
    clean_text = re.sub(r'[，。？！、\s\W]+', '', text)
    for size in range(2, 5):
        for i in range(len(clean_text) - size + 1):
            sub = clean_text[i:i+size]
            if sub not in stop_words and sub not in keywords:
                keywords.append(sub)
    
    return list(set(keywords))


def _score_passage(passage: str, keywords: List[str]) -> float:
    """对段落进行关键词匹配评分"""
    score = 0
    for keyword in keywords:
        count = passage.lower().count(keyword.lower())
        score += count
    return score


# Mock 回答模板
MOCK_RESPONSES = {
    "联系时段": """根据催收合规规则，关于**联系时段**的规定如下：

📅 **允许联系时间：**
- 工作日：**8:00 - 21:00**
- 节假日：**9:00 - 20:00**

⛔ **禁止联系时间：**
- 深夜（21:00之后）
- 凌晨（8:00之前）

**违规后果：** 在禁止时段联系借款人属于中严重度违规，将影响合规评分。

**建议：** 建立系统提醒机制，确保催收人员在规定时段内开展工作。""",

    "威胁": """关于**威胁恐吓**行为，根据合规规则属于**高严重度**违禁行为：

🚫 **严禁行为包括：**
1. 法律威胁：使用"坐牢"、"拘留"、"起诉"等词语
2. 人身威胁：使用"上门"、"找你麻烦"等词语  
3. 伪装执法：谎称自己是警察或执法人员

**法律风险：** 此类行为可能构成违法，面临监管处罚。

**正确做法：** 只陈述合法的信用影响后果，如"逾期将影响您的信用记录"。""",

    "侮辱": """**侮辱性语言**属于高严重度违禁行为：

🚫 **严禁词汇：**
- "废物"、"骗子"、"流氓"、"无赖"等侮辱词汇
- 任何歧视性语言
- 人身攻击性表达

**合规要求：** 
- 保持专业、礼貌的沟通态度
- 使用"您"而非"你"称呼借款人
- 即使借款人情绪激动，也应保持冷静

**培训建议：** 定期开展话术培训，强化文明催收意识。""",
    
    "default": None  # 将使用通用生成逻辑
}


async def chat_stream(
    question: str,
    history: List[Dict[str, str]] = None
) -> AsyncGenerator[str, None]:
    """
    流式问答接口
    """
    llm_mock = os.getenv("LLM_MOCK", "true").lower() == "true"
    
    if llm_mock:
        async for chunk in _mock_chat_stream(question, history):
            yield chunk
    else:
        async for chunk in _llm_chat_stream(question, history):
            yield chunk


async def chat(
    question: str,
    history: List[Dict[str, str]] = None
) -> str:
    """
    同步问答接口
    """
    llm_mock = os.getenv("LLM_MOCK", "true").lower() == "true"
    
    if llm_mock:
        return await _mock_chat(question, history)
    else:
        return await _llm_chat(question, history)


async def _mock_chat(question: str, history: List[Dict] = None) -> str:
    """Mock 问答"""
    import asyncio
    
    # 检查关键词匹配
    for key, response in MOCK_RESPONSES.items():
        if key != "default" and key in question:
            return response
    
    # 搜索相关文档段落
    docs = load_all_documents()
    passages = search_relevant_passages(question, docs)
    
    if passages:
        context = "\n\n".join(passages[:3])
        return f"""根据催收合规规则文档，为您解答：

{_format_mock_answer(question, context)}

---
*以上信息来源于本地合规规则文档。如需了解更多，请查阅完整规则文档。*"""
    else:
        return f"""关于您的问题「{question}」，我在现有规则文档中未找到完全匹配的内容。

建议您：
1. 查阅**催收合规质检规则**文档的相关章节
2. 联系合规部门获取专业指导
3. 参考最新的监管要求和法律法规

如有更具体的问题，欢迎继续提问！"""


def _format_mock_answer(question: str, context: str) -> str:
    """格式化 mock 回答"""
    # 提取关键信息生成回答
    lines = context.split("\n")
    relevant_lines = [l for l in lines if l.strip() and not l.startswith("[")]
    
    answer_parts = []
    for line in relevant_lines[:10]:
        line = line.strip()
        if line.startswith("###"):
            answer_parts.append(f"\n**{line.strip('# ')}**")
        elif line.startswith("-"):
            answer_parts.append(line)
        elif line and not line.startswith("#"):
            answer_parts.append(line)
    
    return "\n".join(answer_parts) if answer_parts else context[:500]


async def _mock_chat_stream(
    question: str,
    history: List[Dict] = None
) -> AsyncGenerator[str, None]:
    """Mock 流式问答"""
    import asyncio
    
    # 获取完整回答
    full_response = await _mock_chat(question, history)
    
    # 模拟流式输出（逐字符/逐词输出）
    words = list(full_response)
    buffer = ""
    
    for i, char in enumerate(words):
        buffer += char
        # 每3个字符发送一次
        if len(buffer) >= 3 or i == len(words) - 1:
            yield f"data: {json.dumps({'type': 'chunk', 'content': buffer})}\n\n"
            buffer = ""
            await asyncio.sleep(0.02)  # 模拟打字机效果
    
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def _llm_chat(question: str, history: List[Dict] = None) -> str:
    """使用真实 LLM 进行问答"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        
        # 加载文档并搜索相关段落
        docs = load_all_documents()
        passages = search_relevant_passages(question, docs)
        context = "\n\n".join(passages) if passages else "未找到相关文档"
        
        system_prompt = f"""你是一个专业的催收合规制度答疑官。你的职责是根据公司的合规规则文档，准确回答催收相关的合规问题。

## 参考文档
{context}

请根据以上文档内容回答用户问题。如果文档中没有相关内容，请明确说明并给出合理建议。
回答要简洁、专业、易于理解，可以使用 Markdown 格式。"""

        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history[-10:]:  # 保留最近10轮对话
                messages.append(msg)
        
        messages.append({"role": "user", "content": question})
        
        response = await client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=messages
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return await _mock_chat(question, history)


async def _llm_chat_stream(
    question: str,
    history: List[Dict] = None
) -> AsyncGenerator[str, None]:
    """使用真实 LLM 进行流式问答"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        
        docs = load_all_documents()
        passages = search_relevant_passages(question, docs)
        context = "\n\n".join(passages) if passages else "未找到相关文档"
        
        system_prompt = f"""你是一个专业的催收合规制度答疑官。

## 参考文档
{context}

请根据以上文档内容回答用户问题，使用 Markdown 格式。"""

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-10:]:
                messages.append(msg)
        messages.append({"role": "user", "content": question})
        
        stream = await client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=messages,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        async for chunk in _mock_chat_stream(question, history):
            yield chunk
