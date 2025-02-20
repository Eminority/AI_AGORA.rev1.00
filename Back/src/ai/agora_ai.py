from ..utils.vectorstore_module import VectorStoreHandler
from ..utils.crawling import DebateDataProcessor
from .ai_instance import AI_Instance
# participant 또는 심판으로 들어갈 ai
class Agora_AI:
    def __init__(self, ai_type: str, ai_instance:AI_Instance, personality:str="", vector_handler: VectorStoreHandler = None):
        """
        Args:
            ai_type (str): AI 모델 타입 (예: 'GEMINI', 'ollama' 등).
            ai_instance: 실제 AI 모델 인스턴스(또는 API를 감싸는 래퍼).
            api_keys (dict): AI_Factory에서 관리하는 API 키 딕셔너리. 
            vector_handler (VectorStoreHandler, optional): 벡터 스토어 핸들러.
        """
        self.ai_type = ai_type
        self.ai_instance = ai_instance
        self.vector_handler = vector_handler if vector_handler is not None else VectorStoreHandler()
        self.personality = personality
        self.vectorstore = None
        self.crawled_data = []

        # API 키를 직접 로드하는 것이 아니라, AI_Factory에서 전달된 값을 사용
        # self.debate_processor = DebateDataProcessor()

        self.set_personality()

    def set_personality(self):
        if self.ai_instance:
            self.ai_instance.set_personality(self.personality)



    def crawling(self, debate_processor:DebateDataProcessor, topic: str):
        """
        주제를 검색하여 기사를 크롤링하고, 결과를 벡터 스토어에 저장한다.

        Args:
            topic (str): 검색할 토론 주제
        """
        articles = debate_processor.get_articles(topic)
        if not articles:
            print("❌ 크롤링된 데이터가 없습니다.")
            return
        self.crawled_data.extend(articles)  # 크롤링된 기사 누적

        # 크롤링한 데이터를 벡터 스토어에 저장
        self.vectorstoring()

    def vectorstoring(self):
        """
        현재까지 수집된 기사(self.crawled_data)를 벡터 스토어에 저장한다.
        
        VectorStoreHandler의 vectorstoring 메서드를 통해 벡터화 및 저장을 수행하고,
        그 결과를 self.vectorstore에 할당한다.
        
        Raises:
            ValueError: 
                - vector_handler가 초기화되지 않았을 경우
                - 크롤링된 데이터가 비어 있거나 유효한 기사 내용이 없을 경우
                - 벡터 스토어 생성에 실패했을 경우
        """
        if self.vector_handler is None:
            raise ValueError(
                "VectorStoreHandler가 초기화되지 않았습니다. "
                "Agora_AI 인스턴스를 생성할 때 vector_handler를 전달했는지 확인하세요."
            )

        # 크롤링된 기사 중 유효한 내용만 필터링
        valid_articles = [
            article for article in self.crawled_data
            if article.get("content", "").strip() and article.get("content", "").strip() != "❌ 본문을 가져오지 못했습니다."
        ]
        if not valid_articles:
            raise ValueError("유효한 기사 내용이 없습니다. 크롤링 데이터를 확인하세요.")

        # 해결방법 2: vectorstoring 메서드가 articles 인수를 받도록 변경되어야 함.
        self.vectorstore = self.vector_handler.vectorstoring(valid_articles)
        
        if self.vectorstore is None:
            raise ValueError("벡터스토어 생성에 실패했습니다.")

    def generate_text(self, prompt: str, k: int = 3, max_tokens: int = 1000): #max_tokens 1000으로 증가
        """
        주어진 prompt와 벡터 스토어를 활용해 텍스트를 생성한다.
        
        Args:
            prompt (str): AI 모델에 전달할 프롬프트
            k (int): 벡터 스토어에서 검색할 상위 문서 수
            max_tokens (int): 생성할 텍스트의 최대 토큰 수

        Returns:
            str: 생성된 텍스트. 
                 ai_type이 GEMINI나 ollama가 아닐 경우 에러 메시지 반환.
        """
        if self.ai_type.upper() == "GEMINI":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "ollama":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "deepseek-r1-distill-llama-70b":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "deepseek-r1-distill-qwen-32b":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "gemma2-9b-it":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama-3.1-8b-instant":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama-3.2-1b-preview":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama-3.2-3b-preview":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama-3.3-70b-specdec":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama-3.3-70b-versatile":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama3-70b-8192":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "llama3-8b-8192":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "mixtral-8x7b-32768":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "qwen-2.5-32b":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        elif self.ai_type.lower() == "qwen-2.5-coder-32b":
            return self.ai_instance.generate_text_with_vectorstore(prompt, self.vectorstore, k=k, max_tokens=max_tokens)
        else:
            return "등록된 형태의 AI가 아닙니다."