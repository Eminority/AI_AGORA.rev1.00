import json
import requests
import subprocess
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

class OllamaRunner:
    def __init__(self, model_name : str, personality : str, role : str, base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.model_installed = False  # 모델 다운로드 상태를 추적하는 변수
        self.personality = personality
        self.role = role

    def is_model_installed(self):
        """현재 설치된 Ollama 모델 목록을 확인하여 해당 모델이 있는지 검사"""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            return self.model_name in result.stdout
        except FileNotFoundError:
            print("❌ Ollama가 설치되지 않았거나 실행할 수 없습니다.")
            return False

    def pull_model(self):
        """모델이 없으면 다운로드 (URL에서 가져와서 설치)"""
        if self.model_installed or self.is_model_installed():  
            self.model_installed = True
            return True
        url = f"{self.base_url}/api/pull"
        response = requests.post(url, json={"name": self.model_name})

        if response.status_code == 200:
            self.model_installed = True
            return True
        else:
            print(f"⚠️ 다운로드 실패: {response.text}")
            return False
        
    # def run_model_interactive(self):
    #     """Ollama 모델을 터미널에서 직접 실행 ('ollama run <model>')"""
    #     if not self.pull_model():
    #         print("❌ 모델 실행 실패!")
    #         return

    #     print(f"🚀 '{self.model_name}' 모델을 실행 중... ")
    #     subprocess.run(["ollama", "run", self.model_name])

    def generate_text(self, prompt : str, temperature : float, max_tokens : int) -> str:
        """프로그래밍 방식으로 텍스트를 입력하면 Ollama 모델이 응답"""
        if not self.pull_model():
            print("❌ 모델 실행 실패!")
            return "Error: Model could not be loaded"

        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model_name, "prompt": prompt}

        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                return f"⚠️ 오류 발생: {response.text}"

            generated_text = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)  # 여기서 변경
                        if "response" in data:
                            generated_text += data["response"] + " "
                    except json.JSONDecodeError:
                        continue  # JSON 파싱 오류 발생 시 무시

            return generated_text.strip()
        
    def generate_text_with_vectorstore(self, user_prompt: str, vectorstore, k: int = 3, max_tokens: int = 100) -> str:
        """
        벡터스토어에서 관련 컨텍스트를 검색한 후, 이를 포함하여 Ollama 모델로 답변을 생성합니다.
        
        :param user_prompt: 사용자 입력 프롬프트
        :param vectorstore: FAISS 등 벡터스토어 인스턴스
        :param k: 유사도 검색 시 반환할 문서 수 (기본값: 3)
        :param max_tokens: 생성할 최대 토큰 수 (Ollama에서 해당 옵션이 지원되는 경우 활용 가능)
        :return: 생성된 텍스트
        """
        # 모델 다운로드 상태를 확인하고 필요 시 다운로드
        if not self.model_installed:
            if not self.pull_model():
                print("❌ 모델 실행 실패!")
                return "Error: Model could not be loaded"

        try:
            # 벡터스토어에서 유사 문서 검색
            search_results = vectorstore.similarity_search(user_prompt, k=k)
            context = "\n".join([doc.page_content for doc in search_results])
        except Exception as e:
            context = ""
            print(f"벡터스토어 검색 실패: {e}")

        # Ollama에 전달할 프롬프트 생성
        full_prompt = f"Context:\n{context}\n\nUser: {user_prompt}"

        # Ollama API 호출 (generate_text 이용)
        response = self.generate_text(full_prompt)
        return response
