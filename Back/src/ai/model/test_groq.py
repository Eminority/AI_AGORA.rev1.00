import requests

class GroqAPI:
    def __init__(self, api_key: str, model: str = "default-model"):
        """
        GroqAPI 인스턴스를 초기화합니다.
        :param api_key: Groq API 인증키
        :param model: 사용할 모델명
        """
        self.api_key = api_key
        self.model = model
        self.personality = ""
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def set_personality(self, personality_text: str):
        """시스템 역할(퍼스낼리티)을 설정합니다."""
        self.personality = personality_text

    def generate_text(self, user_prompt: str, max_tokens: int, temperature: float) -> str:
        # 채팅 방식 요청에서는 "messages" 필드로 시스템 및 사용자 메시지를 전달해야 합니다.
        messages = []
        if self.personality:
            messages.append({
                "role": "system",
                "content": self.personality
            })
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        data = {
            "model": self.model,          # 선택한 모델 ID
            "messages": messages,         # 메시지 리스트
            "max_tokens": max_tokens,     # 생성할 최대 토큰 수
            "temperature": temperature    # 온도 값
        }
        
        # 실제 Groq API 엔드포인트 URL 지정
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                try:
                    content = result["choices"][0]["message"]["content"]
                    # 먼저, </think> 태그가 존재하면 그 뒤 부분을 사용
                    if "</think>" in content:
                        content = content.split("</think>")[-1].strip()
                    # 그렇지 않고, <think>로 시작하면 해당 태그를 제거
                    elif content.startswith("<think>"):
                        content = content[len("<think>"):].strip()
                    return content
                except (KeyError, IndexError):
                    return "응답 없음"
            else:
                return f"API 에러: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"


def real_api_test():
    # 실제 API 테스트를 위한 GroqAPI 인스턴스 생성 (유효한 API 키와 모델명을 사용)
    groq_api = GroqAPI(
        api_key="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", 
        model="qwen-2.5-coder-32b"
    )
    groq_api.set_personality("실제 테스트 퍼스낼리티")
    
    # 실제 API 요청 전송
    result = groq_api.generate_text("안녕하세요, Groq API 실제 테스트입니다.", max_tokens=50, temperature=0.7)
    print("실제 API 응답:", result)

if __name__ == "__main__":
    real_api_test()
