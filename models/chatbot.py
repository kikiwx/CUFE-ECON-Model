import torch
import threading
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import ModelConfig, MODEL_PATH

logger = logging.getLogger(__name__)


class QwenChatBot:
    def __init__(self, model_name=MODEL_PATH):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_loading = True
        self.load_error = None

        self.load_thread = threading.Thread(target=self._load_model)
        self.load_thread.start()

    def _load_model(self):
        """在后台线程中加载模型"""
        try:
            logger.info(f"开始加载模型: {self.model_name}")

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"使用设备: {self.device}")

    
            logger.info("加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            logger.info("加载模型...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            self.is_loading = False
            logger.info("模型加载完成！")

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self.is_loading = False
            self.load_error = str(e)
            raise e

    def is_ready(self):
        """检查模型是否已加载完成"""
        return not self.is_loading and self.model is not None and self.load_error is None

    def get_status(self):
        """获取模型状态"""
        if self.is_loading:
            return "loading"
        elif self.load_error:
            return "error"
        elif self.model is not None:
            return "ready"
        else:
            return "unknown"

    def generate_response(self, user_message, max_new_tokens=None, temperature=None, enable_thinking=None):
        """生成AI回复"""
        if self.is_loading or self.model is None:
            return {
                "content": "模型正在加载中，请稍后再试...",
                "thinking": None,
                "success": False
            }

        if self.load_error:
            return {
                "content": f"模型加载失败: {self.load_error}",
                "thinking": None,
                "success": False
            }

        max_new_tokens = max_new_tokens or ModelConfig.DEFAULT_MAX_TOKENS
        temperature = temperature or ModelConfig.DEFAULT_TEMPERATURE
        enable_thinking = enable_thinking if enable_thinking is not None else ModelConfig.ENABLE_THINKING

        max_new_tokens = min(max_new_tokens, ModelConfig.MAX_TOKENS_LIMIT)
        temperature = max(ModelConfig.TEMPERATURE_MIN, min(temperature, ModelConfig.TEMPERATURE_MAX))

        try:
            messages = [{"role": "user", "content": user_message}]

            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=enable_thinking
            )

            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

            thinking_content = ""
            content = ""

            if enable_thinking:
                try:

                    index = len(output_ids) - output_ids[::-1].index(151668)
                    thinking_content = self.tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
                    content = self.tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
                except ValueError:
                    content = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip("\n")
            else:
                content = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip("\n")

            return {
                "content": content,
                "thinking": thinking_content if enable_thinking else None,
                "success": True
            }

        except Exception as e:
            logger.error(f"生成回复时发生错误: {str(e)}")
            return {
                "content": f"抱歉，生成回复时发生错误: {str(e)}",
                "thinking": None,
                "success": False
            }

    def generate_report_outline(self, topic, requirements):
        """生成报告大纲"""
        prompt = f"""
作为经济学专家，请为以下主题生成一个详细的报告大纲：

主题：{topic}
具体要求：{requirements}

请按以下JSON格式输出大纲，注意摘要部分请使用纯文本格式，避免使用Markdown符号：

{{
    "title": "报告标题",
    "abstract": "报告摘要内容，使用纯文本格式，不要使用星号或其他特殊符号（150字以内）",
    "sections": [
        {{
            "id": "一",
            "title": "章节标题",
            "description": "章节描述和要点"
        }}
    ]
}}

要求：
1. 大纲应该逻辑清晰，层次分明
2. 每个章节都应该有明确的主题和目标
3. 整体结构应该符合学术报告的标准格式
4. 摘要和描述请使用简洁的中文表述，避免使用特殊符号
5. 请确保输出格式为有效的JSON

示例摘要格式：
"本报告主要分析2024年中国宏观经济的发展态势。通过对GDP增长、通胀水平和货币政策的综合分析，评估当前经济形势并提出相关建议。"
"""

        response = self.generate_response(
            prompt,
            max_new_tokens=1500,
            temperature=0.3,
            enable_thinking=False
        )
        return response

    def generate_section_content(self, section_title, section_description, context):
        """生成章节内容"""
        prompt = f"""
作为经济学专家，请为报告章节生成详细内容：

章节标题：{section_title}
章节描述：{section_description}
报告上下文：{context}

请生成该章节的详细内容，要求：
1. 内容应该专业、准确、有深度
2. 结构清晰，逻辑严密
3. 包含具体的数据分析和案例（如果相关）
4. 字数控制在800-1500字之间
5. 使用学术写作风格
6. 避免使用Markdown格式符号，如 # * ** 等
7. 如需强调内容，可以使用「重点内容」的方式标注

请直接输出章节内容，使用纯文本格式。
"""

        response = self.generate_response(
            prompt,
            max_new_tokens=2000,
            temperature=0.4,
            enable_thinking=False
        )
        return response

    def cleanup(self):
        """清理资源"""
        try:
            if self.model is not None:
                del self.model
                self.model = None

            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("模型资源已清理")

        except Exception as e:
            logger.error(f"清理模型资源时发生错误: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()
