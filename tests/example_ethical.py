# ethical_dilemma.py

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew

# 전역 대화 기록 리스트 (LLM 호출 및 에이전트 실행 로그 저장)
conversation_log = []

# .env 파일에서 GEMINI_API_KEY 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

###############################################
# (A) Gemini 전용 커스텀 LLM 클래스
###############################################
class GeminiLLM:
    _is_custom = True
    def __init__(self, api_key):
        self.api_key = api_key
        self._supported_params = {"temperature": True, "max_tokens": True}
        # Gemini 모델 이름: "gemini/gemini-2.0-flash"
        self.model_name = "gemini/gemini-2.0-flash"

    @property
    def supported_params(self):
        return self._supported_params

    def get_supported_params(self):
        return self._supported_params

    def generate(self, prompt: str) -> str:
        # 시뮬레이션 응답 반환 (실제 구현 시 API 호출)
        response = f"[Simulated Gemini 응답: '{prompt}'에 대한 답변]"
        conversation_log.append(f"LLM Generate - Prompt: {prompt}")
        conversation_log.append(f"LLM Generate - Response: {response}")
        return response

    def call(self, prompt: str, **kwargs):
        response = self.generate(prompt)
        return {"choices": [{"message": {"content": response}}]}

    def __call__(self, prompt: str, **kwargs):
        return self.call(prompt, **kwargs)

###############################################
# (B) LoggingAgent 정의 (CrewAI Agent 확장)
###############################################
class LoggingAgent(Agent):
    def execute_task(self, *args, **kwargs):
        # pydantic 모델을 통해 에이전트 이름 접근
        name = self.model_dump().get("name", "Unknown")
        conversation_log.append(f"[시작] Agent '{name}' 작업 시작.")
        result = super().execute_task(*args, **kwargs)
        conversation_log.append(f"[완료] Agent '{name}' 작업 결과: {result}")
        return result

###############################################
# (C) 에이전트 정의
###############################################
# 윤리적 입장을 가진 에이전트
ethical_agent = LoggingAgent(
    name="Ethical_Agent",
    role="윤리적 인격",
    goal="누군가의 감정을 보호하기 위해 거짓말을 하는 것은 기본적으로 부정적이라고 주장한다. 정직이 최우선이며, 진실을 말하는 것이 신뢰를 구축한다고 믿는다.",
    backstory="항상 정직을 중요시하는 윤리적 인격을 가진 AI 에이전트.",
    llm=GeminiLLM(gemini_api_key)
)

# 다소 비윤리적 입장을 가진 에이전트
unethical_agent = LoggingAgent(
    name="Unethical_Agent",
    role="비윤리적 인격",
    goal="때로는 누군가의 감정을 보호하기 위해 거짓말을 하는 것이 정당할 수 있다고 주장한다. 상황에 따라 결과가 중요하다고 본다.",
    backstory="결과지향적이고, 때로는 윤리적 기준을 유연하게 해석하는 인격을 가진 AI 에이전트.",
    llm=GeminiLLM(gemini_api_key)
)

# 조정자(Moderator) 에이전트: 두 입장을 조율하고 결론을 도출
moderator_agent = LoggingAgent(
    name="Moderator_Agent",
    role="조정자",
    goal="윤리적 입장과 비윤리적 입장을 종합하여, 최종 결론과 합리적인 중재 의견을 제시한다.",
    backstory="공정하고 중립적인 입장을 유지하며, 두 입장 간 균형 있는 결론을 도출하는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

###############################################
# (D) 작업(Task) 정의 (입력값 {ethical_dilemma} 적용)
###############################################
# 윤리적 입장 에이전트의 발언 태스크
ethical_task = Task(
    description="윤리적 관점에서 '{ethical_dilemma}'에 대해 논의하고, 정직과 진실의 가치를 강조하는 의견을 제시한다.",
    agent=ethical_agent,
    expected_output="윤리적 입장에서의 논거와 결론"
)

# 비윤리적 입장 에이전트의 발언 태스크
unethical_task = Task(
    description="비윤리적 관점에서 '{ethical_dilemma}'에 대해 논의하고, 상황에 따라 유연한 윤리 기준을 제시하는 의견을 제시한다.",
    agent=unethical_agent,
    expected_output="비윤리적 입장에서의 논거와 결론"
)

# 조정자 에이전트의 종합 태스크: 두 입장의 논의를 종합하여 최종 결론 도출
moderator_task = Task(
    description="윤리적 입장과 비윤리적 입장의 논의를 종합하여, '{ethical_dilemma}'에 대한 최종 결론과 중재 의견을 제시한다.",
    agent=moderator_agent,
    expected_output="최종 결론과 중재 의견"
)

###############################################
# (E) Crew 구성 (manager_agent는 agents 리스트에서 제외)
###############################################
# hierarchical 모드: 조정자(Moderator)가 매니저 역할 수행
ethical_crew = Crew(
    agents=[ethical_agent, unethical_agent],
    tasks=[ethical_task, unethical_task],
    process="hierarchical",
    manager_agent=moderator_agent,  # 여기서 조정자가 전체 과정을 조율
    verbose=True
)

###############################################
# (F) 실행 예시 (main 함수)
###############################################
if __name__ == "__main__":
    # 예시 입력값: 윤리 문제
    inputs = {
        "ethical_dilemma": "누군가의 감정을 보호하기 위해 거짓말을 하는 것이 윤리적인가?"
    }
    
    # 전체 크루 실행 (각 태스크의 description 내 {ethical_dilemma}가 입력값으로 치환됨)
    result = ethical_crew.kickoff(inputs=inputs)
    
    # 결과 및 전체 대화 로그를 텍스트 파일로 저장
    with open("ethical_dilemma_log.txt", "w", encoding="utf-8") as f:
        f.write("=== 윤리 문제 토론 프로세스 로그 ===\n\n")
        f.write("최종 결론:\n" + str(result) + "\n\n")
        f.write("토론 중간 로그:\n")
        for line in conversation_log:
            f.write(line + "\n")
    
    print("\n=== Done! ===")
    print("전체 토론 로그와 최종 결과가 'ethical_dilemma_log.txt'에 저장되었습니다.")
