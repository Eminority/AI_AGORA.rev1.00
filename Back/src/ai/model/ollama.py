import json
import requests
import subprocess
from ..ai_instance import AI_Instance

class OllamaRunner(AI_Instance):
    def __init__(self, model_name: str = "default-model"):
        # 상위 클래스에서 model_name과 personality를 등록합니다.
        super().__init__(model_name=model_name)
        self.model_name = model_name  # 모델 다운로드 상태를 추적하는 변수
        self.personality = ""
        # 이미 추가한 헤더 외에 필수 헤더 설정
        self.headers = {"Content-Type": "application/json"}

    def set_personality(self, personality_text: str):
        """
        시스템 역할(지침)을 설정하여 모든 프롬프트 앞에 추가할 텍스트로 사용합니다.
        """
        self.personality = personality_text

    def extract_content(self, result: dict) -> str:
        """
        API 응답(result)에서 텍스트 콘텐츠를 추출합니다.
        우선 choices[0]["message"]["content"]를 시도하고, 없으면 choices[0]["text"]를 사용합니다.
        또한, <think> 태그가 있다면 이를 제거합니다.
        """
        try:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
            elif "text" in choice:
                content = choice["text"]
            else:
                content = "응답 없음"
            # <think> 태그 처리
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            elif content.startswith("<think>"):
                content = content[len("<think>"):].strip()
            return content
        except Exception as e:
            return f"응답 없음: {e}"

    def generate_text(self, user_prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Ollama 모델을 사용하여 텍스트를 생성합니다.
        personality가 설정되어 있다면 프롬프트 앞에 추가합니다.
        """
        full_prompt = user_prompt
        if self.personality:
            full_prompt = f"personality: {self.personality}\n{user_prompt}"
        data = {
            "model": self.model_name,
            "prompt": full_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        url = "http://localhost:11434/api/generate"
        try:
            response = requests.post(url, json=data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                return self.extract_content(result)
            else:
                return f"API 에러: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_text_with_vectorstore(self, user_prompt: str, max_tokens: int, temperature: float, vectorstore, k: int) -> str:
        """
        벡터스토어를 이용하여 유사 문서를 검색한 후, 컨텍스트와 함께 텍스트를 생성합니다.
        """
        try:
            search_results = vectorstore.similarity_search(user_prompt, k=k)
            context = "\n".join([doc.page_content for doc in search_results])
        except Exception as e:
            context = ""
            print(f"벡터스토어 검색 실패: {e}")

        if self.personality:
            full_prompt = f"System: {self.personality}\nContext: {context}\nUser: {user_prompt}"
        else:
            full_prompt = f"Context: {context}\nUser: {user_prompt}"

        url = "http://localhost:11434/api/generate"
        data = {
            "model": self.model_name,
            "prompt": full_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            response = requests.post(url, json=data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                return self.extract_content(result)
            else:
                return f"API 에러: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"
