"""
ASR 工具 - 语音转文字
支持 mock 模式和真实 whisper 模式
"""
import os
import random
from typing import Optional

# Mock 样本文本 - 包含不同合规程度的催收对话
MOCK_TRANSCRIPTS = [
    """您好，我是某某金融公司的催收专员，工号A001。
请问您是张三先生吗？我联系您是关于您2024年1月15日的5000元贷款还款事宜。
您的贷款已经逾期30天了，请问您什么时候方便还款？
我们可以为您提供分期还款方案，您有什么困难可以告诉我，我们一起想办法解决。""",

    """喂，你是张三吗？你欠了我们的钱，你知不知道？
你再不还款，我就让你坐牢！你这个骗子！
我要打电话给你们公司领导，让你在单位抬不起头！
你现在必须立刻还款，否则后果自负！""",

    """您好，这里是信达金融，我是客服专员李四，工号B002。
张先生，您好，我这里显示您有一笔2000元的贷款已逾期15天。
请问您是否遇到了什么还款困难？
我们可以帮您申请延期或者制定分期方案，您方便说说情况吗？
另外，如果您有任何疑问，也可以拨打我们的客服热线400-xxx-xxxx进行投诉或咨询。""",

    """你好，我叫王五，我是执法人员，你的案件已经被移交到我们这里处理了。
如果你今天不还钱，明天就要来派出所报到。
你欠的钱加上利息现在是10000元，必须今天还清。
你这个废物，借钱不还，真是无赖！""",
]


def transcribe(audio_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    将音频数据转换为文字
    
    Args:
        audio_bytes: 音频文件的字节数据
        filename: 原始文件名（可选）
    
    Returns:
        转录后的文字内容
    """
    asr_mock = os.getenv("ASR_MOCK", "true").lower() == "true"
    
    if asr_mock:
        return _mock_transcribe(audio_bytes, filename)
    else:
        return _whisper_transcribe(audio_bytes, filename)


def _mock_transcribe(audio_bytes: bytes, filename: Optional[str] = None) -> str:
    """Mock 转录 - 根据文件大小随机选择样本"""
    # 根据文件大小选择不同的 mock 文本，模拟真实性
    size = len(audio_bytes)
    index = size % len(MOCK_TRANSCRIPTS)
    
    transcript = MOCK_TRANSCRIPTS[index]
    return transcript.strip()


def _whisper_transcribe(audio_bytes: bytes, filename: Optional[str] = None) -> str:
    """使用 OpenAI Whisper 进行真实转录"""
    try:
        import whisper
        import tempfile
        import os
        
        # 确定文件扩展名
        ext = ".wav"
        if filename:
            _, ext = os.path.splitext(filename)
            if not ext:
                ext = ".wav"
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            model = whisper.load_model("base")
            result = model.transcribe(tmp_path, language="zh")
            return result["text"].strip()
        finally:
            os.unlink(tmp_path)
            
    except ImportError:
        # whisper 未安装，回退到 mock
        return _mock_transcribe(audio_bytes, filename)
    except Exception as e:
        return f"[转录失败: {str(e)}] " + _mock_transcribe(audio_bytes, filename)
