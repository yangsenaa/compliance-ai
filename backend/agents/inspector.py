"""
智能质检官 Agent
负责对催收通话文本进行合规质检，识别违规行为并评分
"""
import os
import json
import random
import re
from pathlib import Path
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"

# 违规关键词规则库（用于 mock 模式）
VIOLATION_RULES = [
    {
        "keywords": ["坐牢", "拘留", "起诉", "逮捕", "派出所", "执法", "警察"],
        "rule": "1.1 威胁恐吓 - 法律威胁",
        "severity": "高",
        "explanation": "使用了非法律事实的法律威胁，属于严禁行为"
    },
    {
        "keywords": ["上门", "找你麻烦", "派人"],
        "rule": "1.1 威胁恐吓 - 人身威胁",
        "severity": "高",
        "explanation": "使用了人身威胁语言，属于严禁行为"
    },
    {
        "keywords": ["公司领导", "你们公司", "单位", "同事", "家人", "家属", "父母"],
        "rule": "1.2 骚扰第三方",
        "severity": "高",
        "explanation": "威胁联系借款人第三方关系人，属于严禁行为"
    },
    {
        "keywords": ["废物", "骗子", "流氓", "无赖", "混蛋", "垃圾"],
        "rule": "1.3 侮辱性语言",
        "severity": "高",
        "explanation": "使用侮辱性词汇，属于严禁行为"
    },
    {
        "keywords": ["必须立刻", "马上还", "今天必须", "立即还款"],
        "rule": "2.3 还款协商 - 强迫还款",
        "severity": "中",
        "explanation": "强迫借款人立即还款，未给予合理缓冲期"
    },
    {
        "keywords": ["后果自负", "否则后果"],
        "rule": "2.2 话术规范 - 威胁性表达",
        "severity": "中",
        "explanation": "使用模糊威胁性表达，不符合话术规范"
    },
]

# 正面合规关键词（用于提高评分）
COMPLIANCE_KEYWORDS = [
    "工号", "公司名称", "分期", "困难", "方案", "投诉渠道", 
    "您好", "请问", "方便", "帮您"
]


def load_rules_document() -> str:
    """加载本地质检规则文档"""
    rules_path = DATA_DIR / "compliance_rules.md"
    if rules_path.exists():
        return rules_path.read_text(encoding="utf-8")
    return "规则文档未找到"


def load_all_documents() -> dict:
    """加载 data 目录下所有文档"""
    docs = {}
    for md_file in DATA_DIR.glob("*.md"):
        docs[md_file.stem] = md_file.read_text(encoding="utf-8")
    return docs


def _mock_inspect(text: str) -> dict:
    """
    Mock 质检逻辑：基于关键词规则进行违规检测
    """
    violations = []
    
    # 检测违规关键词
    for rule in VIOLATION_RULES:
        for keyword in rule["keywords"]:
            # 查找关键词位置
            start = 0
            while True:
                pos = text.find(keyword, start)
                if pos == -1:
                    break
                
                # 提取包含关键词的句子
                sentence_start = max(0, text.rfind("\n", 0, pos) + 1)
                sentence_end = text.find("\n", pos)
                if sentence_end == -1:
                    sentence_end = len(text)
                
                sentence = text[sentence_start:sentence_end].strip()
                
                # 避免重复添加同一句子的同一规则
                already_added = any(
                    v["sentence"] == sentence and v["rule"] == rule["rule"]
                    for v in violations
                )
                
                if not already_added and sentence:
                    violations.append({
                        "sentence": sentence,
                        "start": sentence_start,
                        "end": sentence_end,
                        "rule": rule["rule"],
                        "severity": rule["severity"],
                        "explanation": rule["explanation"]
                    })
                
                start = pos + len(keyword)
    
    # 计算合规评分
    score = _calculate_score(text, violations)
    
    # 生成总结
    summary = _generate_summary(violations, score)
    
    return {
        "original_text": text,
        "violations": violations,
        "score": score,
        "summary": summary
    }


def _calculate_score(text: str, violations: list) -> int:
    """计算合规评分（0-100）"""
    base_score = 100
    
    # 根据违规严重度扣分
    for v in violations:
        if v["severity"] == "高":
            base_score -= 20
        elif v["severity"] == "中":
            base_score -= 10
        elif v["severity"] == "低":
            base_score -= 5
    
    # 正面关键词加分（上限10分）
    positive_count = sum(1 for kw in COMPLIANCE_KEYWORDS if kw in text)
    bonus = min(10, positive_count * 2)
    
    score = max(0, min(100, base_score + bonus))
    return score


def _generate_summary(violations: list, score: int) -> str:
    """生成质检总结"""
    if score >= 90:
        level = "优秀"
        desc = "本次通话整体合规，催收行为规范，建议继续保持。"
    elif score >= 70:
        level = "合格"
        desc = "本次通话基本合规，但存在部分需要改进的地方，请注意规范用语。"
    elif score >= 50:
        level = "待改进"
        desc = "本次通话存在多处违规行为，需要加强培训和监督。"
    else:
        level = "不合格"
        desc = "本次通话存在严重违规行为，需要立即整改，可能面临合规处罚。"
    
    high_count = sum(1 for v in violations if v["severity"] == "高")
    mid_count = sum(1 for v in violations if v["severity"] == "中")
    low_count = sum(1 for v in violations if v["severity"] == "低")
    
    detail = f"发现违规：高严重度 {high_count} 处，中严重度 {mid_count} 处，低严重度 {low_count} 处。"
    
    return f"【{level}】合规评分：{score}分。{detail}{desc}"


async def inspect_text_stream(text: str) -> AsyncGenerator[str, None]:
    """
    流式质检 - 逐步输出分析过程
    """
    llm_mock = os.getenv("LLM_MOCK", "true").lower() == "true"
    
    if llm_mock:
        # Mock 流式输出
        yield "data: " + json.dumps({"type": "status", "message": "正在加载质检规则..."}) + "\n\n"
        
        import asyncio
        await asyncio.sleep(0.3)
        
        yield "data: " + json.dumps({"type": "status", "message": "正在分析文本内容..."}) + "\n\n"
        await asyncio.sleep(0.5)
        
        result = _mock_inspect(text)
        
        yield "data: " + json.dumps({"type": "status", "message": f"检测到 {len(result['violations'])} 处违规..."}) + "\n\n"
        await asyncio.sleep(0.3)
        
        yield "data: " + json.dumps({"type": "result", "data": result}) + "\n\n"
        yield "data: " + json.dumps({"type": "done"}) + "\n\n"
    else:
        # 真实 LLM 调用
        async for chunk in _llm_inspect_stream(text):
            yield chunk


async def inspect_text(text: str) -> dict:
    """
    同步质检接口
    """
    llm_mock = os.getenv("LLM_MOCK", "true").lower() == "true"
    
    if llm_mock:
        return _mock_inspect(text)
    else:
        return await _llm_inspect(text)


async def _llm_inspect(text: str) -> dict:
    """使用真实 LLM 进行质检"""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        
        rules = load_rules_document()
        
        prompt = f"""你是一个专业的催收合规质检专家。请根据以下质检规则，对催收通话文本进行质检分析。

## 质检规则
{rules}

## 待检测文本
{text}

请以 JSON 格式返回质检结果，格式如下：
{{
  "original_text": "原始文本",
  "violations": [
    {{
      "sentence": "违规句子",
      "start": 起始位置,
      "end": 结束位置,
      "rule": "违反的规则",
      "severity": "高/中/低",
      "explanation": "违规原因说明"
    }}
  ],
  "score": 合规评分(0-100),
  "summary": "总体质检结论"
}}

只返回 JSON，不要有其他内容。"""

        response = await client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["original_text"] = text
        return result
        
    except Exception as e:
        # 回退到 mock 模式
        result = _mock_inspect(text)
        result["summary"] = f"[LLM调用失败，使用规则引擎] {result['summary']}"
        return result


async def _llm_inspect_stream(text: str) -> AsyncGenerator[str, None]:
    """使用真实 LLM 进行流式质检"""
    # 先返回状态
    yield "data: " + json.dumps({"type": "status", "message": "正在调用 LLM 分析..."}) + "\n\n"
    
    result = await _llm_inspect(text)
    yield "data: " + json.dumps({"type": "result", "data": result}) + "\n\n"
    yield "data: " + json.dumps({"type": "done"}) + "\n\n"
