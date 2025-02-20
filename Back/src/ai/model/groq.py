import requests
from groq import Groq

class GroqAPI:
    def __init__(self, api_key: str, model_name: str = "default-model"):
        """
        GroqAPI 인스턴스를 초기화합니다.

        :param api_key: Groq API 인증키
        :param model_name: 기본으로 사용할 모델 ID (예: 'model_name_small', 'model_name_large' 등)
        """
        self.api_key = api_key
        self.groq_client = Groq(api_key=api_key)
        self.model_name = model_name
        self.personality = ""  # 기본 시스템 역할 (없으면 빈 문자열)
        # Groq API 엔드포인트 (실제 엔드포인트로 수정)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def set_personality(self, personality_text: str):
        """
        시스템 역할(지침)을 설정하여 모든 프롬프트에 선행하는 텍스트로 사용합니다.

        :param personality_text: 시스템 역할 또는 지침 텍스트
        """
        self.personality = personality_text


    def generate_text(self, user_prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """
        Groq 모델을 사용하여 텍스트를 생성합니다.

        :param user_prompt: 사용자 입력 프롬프트
        :param max_tokens: 생성할 최대 토큰 수
        :param temperature: 텍스트 생성 온도 값
        :return: 생성된 텍스트 또는 에러 메시지
        """
        # personality가 있으면 프롬프트 앞에 추가
        full_prompt = user_prompt
        if self.personality:
            full_prompt = f"personality: {self.personality}\n{user_prompt}"

        data = {
            "model_name": self.model_name,          # 선택한 모델 ID
            "prompt": full_prompt,              # 최종 프롬프트
            "max_tokens": max_tokens,           # 생성할 최대 토큰 수
            "temperature": temperature          # 온도 값
        }

        try:
            response = requests.post(json=data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                # 응답 필드는 실제 API 스펙에 맞게 수정
                return result.get("text", "응답 없음")
            else:
                return f"API 에러: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_text_with_vectorstore(self, user_prompt: str, vectorstore, k: int = 3, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """
        벡터스토어에서 유사한 컨텍스트를 검색한 후, 이를 포함하여 Groq API로 답변을 생성합니다.

        :param user_prompt: 사용자 입력 프롬프트
        :param vectorstore: FAISS 등으로 구성된 벡터스토어 인스턴스 (문서 객체는 'page_content' 속성을 가짐)
        :param k: 벡터스토어 유사도 검색 시 반환할 문서 수 (기본값: 3)
        :param max_tokens: 생성할 최대 토큰 수
        :param temperature: 텍스트 생성 온도 값
        :return: 생성된 텍스트 또는 에러 메시지
        """
        try:
            # 벡터스토어에서 유사 문서 검색 (각 문서는 page_content 속성을 가진다고 가정)
            search_results = vectorstore.similarity_search(user_prompt, k=k)
            context = "\n".join([doc.page_content for doc in search_results])
        except Exception as e:
            context = ""
            print(f"벡터스토어 검색 실패: {e}")

        if self.personality:
            full_prompt = f"System: {self.personality}\nContext: {context}\nUser: {user_prompt}"
        else:
            full_prompt = f"Context: {context}\nUser: {user_prompt}"

        # data = {
        #     "model_name": self.model_name,
        #     "prompt": full_prompt,
        #     "max_tokens": max_tokens,
        #     "temperature": temperature
        # }

        # try:
        #     response = requests.post(json=data, headers=self.headers)
        #     if response.status_code == 200:
        #         result = response.json()
        #         return result.get("text", "답변 없음")
        #     else:
        #         return f"API 에러: {response.status_code} - {response.text}"
        # except Exception as e:
        #     return f"Error: {str(e)}"

        result = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role":"user",
                    "content": full_prompt
                }
            ],
            model = self.model_name
        )
        return result.choices[0].message.content.split("</think>")[-1]

    def close_connection(self):
        """
        Groq API 연결을 해제합니다.
        (필요에 따라 API 연결 종료에 관한 로직을 추가합니다.)
        """
        # Groq API는 stateless하므로 별도의 연결 해제가 필요하지 않을 수 있음.
        self.api_key = None
        self.headers["Authorization"] = ""
      
