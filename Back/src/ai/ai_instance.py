from abc import ABC, abstractmethod

class AI_Instance(ABC):
    """
    gemini, groq, ollama 등을 사용하기 좋게 하나로 묶어주는 부모 클래스
    """
    def __init__(self, api_key: str=None, model_name:str="", personality:str = ""):
        
        self.api_key = api_key
        self.model_name = model_name
        self.personality = personality

    @abstractmethod
    def generate_text(self, user_prompt: str, max_tokens: int) -> str:
        """
        prompt를 받아 text를 출력해주는 메서드.
        """
        pass

    @abstractmethod
    def generate_text_with_vectorstore(self, user_prompt: str, vectorstore, max_tokens: int, k: int = 3) -> str:
        """
        vectorstore기반으로 prompt를 받아 text를 출력해주는 메서드.
        """
        pass

    @abstractmethod
    def set_personality(self, personaliry_text:str):
        pass