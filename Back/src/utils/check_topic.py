import google.generativeai as genai
from .ai_module.gemini import GeminiAPI 

class CheckTopic :
    def __init__(self, api_key : str):
        self.model = genai.GenerativeModel('gemini-pro')
        self.gemini_api = GeminiAPI(api_key)

    def checktopic(self, topic: str) -> bool:
        """
        LLM을 사용하여 주제가 토론 가능 여부를 판별합니다.
        :param topic: 사용자가 입력한 토론 주제
        :return: True (토론 가능) / False (토론 불가능)
        """
        prompt = f"""
        Determine if the following topic is debatable. 
        A debatable topic must have valid opposing arguments for both sides. 
        If the topic is too subjective or lacks logical opposition, return False. 
        Respond only with 'True' or 'False'.
        
        Topic: "{topic}"
        """

        try:
            response = self.gemini_api.generate_text(prompt, max_tokens=5)  # 최대 5토큰 (True/False 응답만 받도록)
            result = response.strip().lower()
            return result == "true"
        except Exception as e:
            print(f"Error in is_debatable_topic: {e}")
            return False  # 오류 시 기본값 False 반환
