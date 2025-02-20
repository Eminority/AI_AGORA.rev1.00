from .model.gemini import GeminiAPI
from .model.ollama import OllamaRunner
from .model.groq import GroqAPI

class AI_Factory:
    def __init__(self, api_keys: dict):
        """
        필요한 API 키를 저장합니다.
        예: {"GEMINI": "GEMINI_API_KEY", "GROQ": "GROQ_API_KEY"}
        """
        self.api = api_keys

        # Groq에서 지원하는 모델 목록
        self.groq_models = {
            "deepseek-r1-distill-llama-70b",
            "deepseek-r1-distill-qwen-32b",
            "gemma2-9b-it",
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "llama-3.3-70b-specdec",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "qwen-2.5-32b",
            "qwen-2.5-coder-32b"
        }

        # Ollama에서 사용할 수 있는 모델 목록
        self.ollama_models = [
            "phi3:mini",
            "llama3.2",
            "deepseek-r1:7b",
            "exaone3.5:7.8b",
            "exaone3.5",
            "mistral",
            "llama3",
        ]

    def create_ai_instance(self, ai_type: str):
        """
        AI 유형 또는 모델 이름을 기반으로 적절한 인스턴스를 생성하는 메서드
        :param ai_type: "ollama", "GEMINI", "GROQ" 또는 모델명 자체
        :return: 해당 AI 인스턴스 또는 None
        """
        # 사용자가 모델 이름을 직접 입력한 경우
        if ai_type in self.groq_models:
            if "GROQ" in self.api:
                return GroqAPI(self.api["GROQ"], model_name=ai_type)
            else:
                print("GROQ API 키가 제공되지 않았습니다.")
                return None

        if ai_type in self.ollama_models:
            return OllamaRunner(model_name=ai_type)

        # Gemini API 모델
        if ai_type == "GEMINI":
            if "GEMINI" in self.api:
                return GeminiAPI(self.api["GEMINI"])
            else:
                print("GEMINI API 키가 제공되지 않았습니다.")
                return None

        # 지원되지 않는 AI 유형
        print("지원되지 않는 AI 유형 또는 모델 이름입니다.")
        return None
