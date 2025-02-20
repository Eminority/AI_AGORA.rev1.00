from langchain_community.retrievers import WikipediaRetriever
from langchain.prompts import PromptTemplate
import google.generativeai as genai 

class DetectPersona:
    """
    객체 정보를 검색하고 성격을 분석하여 DB에 저장하는 클래스.
    - Wikipedia 또는 GEMINI API를 활용하여 정보 검색
    - 성격 분석을 GEMINI API 또는 Local 모델(Ollama) 중 선택 가능
    - 결과를 MongoDB에 자동 저장
    """

    def __init__(self, AI_API_KEY=None):
        self.source = "wikipedia"  # 검색 소스: "wikipedia" 또는 "gemini"
        self.local_model = "llama3.2"  # Local 모델 이름
        self.retriever = WikipediaRetriever()

        if AI_API_KEY:
            genai.configure(api_key=AI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')


    def get_traits(self, object_name: str) -> str:
        """
        객체 정보를 검색하고 성격 분석을 수행.
        - DB에 해당 객체 정보가 존재하면 그대로 반환.
        - 존재하지 않으면 새로 분석 후 DB에 저장.
        """
        # 🔍 정보 검색 단계
        docs = self.retriever.invoke(object_name)
        if not docs:
            return "❌ 해당 객체에 대한 정보를 찾을 수 없습니다."
        context = docs[0].page_content
        
        # 🔍 성격 분석 (Local LLM 또는 GEMINI)
        prompt_template = PromptTemplate(
            input_variables=["object_name", "context"],
            template="Based on the following information, describe the personality traits of {object_name} in only 1 briefly and short sentence words: {context}"
        )
        final_prompt = prompt_template.format(object_name=object_name, context=context)
        # local llm 사용할 경우
        # traits = self.local_llm.invoke(final_prompt)  # ✅ 최신 메서드 사용
        response = self.gemini_model.generate_content(final_prompt)
        traits = response.text if response else "❌ 성격 분석 실패."
        return traits