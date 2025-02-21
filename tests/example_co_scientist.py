# example_co_scientist.py

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew

# 전역 로그 리스트 (LLM 호출 및 에이전트 실행 로그를 저장)
conversation_log = []

# .env 파일에서 환경 변수 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

###############################################
# (A) Gemini 전용 커스텀 LLM 클래스 (개선됨)
###############################################
class GeminiLLM:
    _is_custom = True  # 커스텀 LLM임을 명시
    def __init__(self, api_key):
        self.api_key = api_key
        self._supported_params = {"temperature": True, "max_tokens": True}
        # Gemini 모델 이름을 Gemini-2.0-flash로 지정 (litellm가 요구하는 "provider/model" 형식)
        self.model_name = "gemini/gemini-2.0-flash"

    @property
    def supported_params(self):
        return self._supported_params

    def get_supported_params(self):
        return self._supported_params

    def generate(self, prompt: str) -> str:
        """
        실제 Gemini API 호출 대신, 입력 프롬프트에 대한 시뮬레이션 응답을 생성합니다.
        LLM 호출 시 프롬프트와 응답을 전역 conversation_log에 기록합니다.
        """
        response = f"[Simulated Gemini 응답: '{prompt}'에 대한 답변]"
        conversation_log.append(f"LLM Generate - Prompt: {prompt}")
        conversation_log.append(f"LLM Generate - Response: {response}")
        return response

    def call(self, prompt: str, **kwargs):
        """
        CrewAI 내부에서 LLM 호출 시 사용하는 인터페이스.
        OpenAI API와 유사한 딕셔너리 구조로 응답을 반환합니다.
        """
        response = self.generate(prompt)
        return {"choices": [{"message": {"content": response}}]}

    def __call__(self, prompt: str, **kwargs):
        """
        객체를 함수처럼 호출할 수 있도록 __call__ 메서드를 오버라이드합니다.
        이를 통해 CrewAI 내부에서 우리의 custom LLM이 직접 호출되도록 합니다.
        """
        return self.call(prompt, **kwargs)

###############################################
# (B) LoggingAgent 정의 (CrewAI Agent 확장)
###############################################
class LoggingAgent(Agent):
    """
    각 Agent가 작업을 시작/종료할 때, 그리고 작업 결과를 전역 로그에 기록한다.
    """
    def execute_task(self, *args, **kwargs):
        name = self.model_dump().get("name", "Unknown")
        conversation_log.append(f"[시작] Agent '{name}' 작업 시작.")
        result = super().execute_task(*args, **kwargs)
        conversation_log.append(f"[완료] Agent '{name}' 작업 결과: {result}")
        return result

###############################################
# (C) 에이전트 정의
###############################################
# Supervisor Agent: 전체 연구 과정을 기획하고 특화 에이전트에게 작업을 배분
supervisor_agent = LoggingAgent(
    name="Supervisor_Agent",
    role="Supervisor",
    goal="연구 목표 '{research_goal}'를 바탕으로 전체 과정을 기획하고, 특화 에이전트들에게 작업을 분배하여 종합적인 연구 보고서를 완성한다.",
    backstory="다양한 AI 공동 연구자를 관리하며, 전체 프로세스를 감독하는 책임자 역할을 수행하고, 작업을 효율적으로 진행한다.",
    llm=GeminiLLM(gemini_api_key)
)

# Generation Agent: 아이디어 생성 및 초안 작성
generation_agent = LoggingAgent(
    name="Generation_Agent",
    role="Generation",
    goal="연구 목표 '{research_goal}'에 대해 창의적인 아이디어와 가설 초안을 생성한다.",
    backstory="연구 주제와 관련된 다양한 개념을 빠르게 생성하는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

# Reflection Agent: 생성된 아이디어를 비판적으로 검토
reflection_agent = LoggingAgent(
    name="Reflection_Agent",
    role="Reflection",
    goal="생성된 아이디어에 대해 '{research_goal}'와 관련된 잠재적 오류와 개선점을 검토한다.",
    backstory="아이디어의 타당성과 논리적 결함을 파악하여 품질을 높이는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

# Ranking Agent: 아이디어를 우선순위로 정리
ranking_agent = LoggingAgent(
    name="Ranking_Agent",
    role="Ranking",
    goal="검토된 아이디어를 '{research_goal}'에 맞춰 우선순위에 따라 정렬한다.",
    backstory="아이디어의 영향력과 실현 가능성을 평가하여 순위를 매기는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

# Evolution Agent: 아이디어를 발전시켜 더욱 완성도 높게 변형
evolution_agent = LoggingAgent(
    name="Evolution_Agent",
    role="Evolution",
    goal="우선순위가 높은 아이디어를 '{research_goal}'에 맞춰 발전시켜 개선한다.",
    backstory="새로운 관점과 추가 실험 제안을 통해 아이디어를 업그레이드하는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

# Proximity Agent: 아이디어 간 연관성을 분석
proximity_agent = LoggingAgent(
    name="Proximity_Agent",
    role="Proximity",
    goal="발전된 아이디어 간 연관성과 외부 연구와의 유사성을 분석하여 '{research_goal}'의 전체 맥락을 제시한다.",
    backstory="분산된 정보를 연결해 전체 그림을 제시하는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

# Meta-review Agent: 전체 과정을 종합적으로 리뷰
meta_review_agent = LoggingAgent(
    name="Meta_Review_Agent",
    role="Meta-review",
    goal="최종 결과물을 종합적으로 검토하여 '{research_goal}'에 부합하는 피드백을 제공한다.",
    backstory="여러 에이전트의 결과물을 종합해 보고서의 일관성과 품질을 유지하는 전문가.",
    llm=GeminiLLM(gemini_api_key)
)

###############################################
# (D) 작업(Task) 정의 (각 태스크에 입력값 {research_goal} 적용)
###############################################
supervisor_task = Task(
    description="연구 목표 '{research_goal}'를 받아들인 후, Generation/Reflection/Ranking/Evolution/Proximity/Meta-review 순으로 작업을 분배하고 최종 보고서를 작성한다.",
    agent=supervisor_agent,
    expected_output="각 특화 에이전트의 결과물을 종합한 연구 보고서 (가설, 아이디어, 검토 사항 등)"
)

generation_task = Task(
    description="연구 목표 '{research_goal}'에 대한 가설이나 개념을 3~5가지 정도 창의적으로 생성한다.",
    agent=generation_agent,
    expected_output="생성된 가설/아이디어 리스트"
)

reflection_task = Task(
    description="생성된 아이디어에 대해 '{research_goal}'와 관련된 잠재적 오류와 개선점을 제시한다.",
    agent=reflection_agent,
    expected_output="개선사항 및 추가 고려사항 리스트"
)

ranking_task = Task(
    description="검토된 아이디어를 '{research_goal}'에 맞춰 우선순위에 따라 정렬한다.",
    agent=ranking_agent,
    expected_output="우선순위가 매겨진 아이디어 목록"
)

evolution_task = Task(
    description="우선순위가 높은 아이디어를 '{research_goal}'에 맞춰 발전시켜 더욱 완성도 높은 형태로 변형한다.",
    agent=evolution_agent,
    expected_output="발전된 아이디어(가설) 목록"
)

proximity_task = Task(
    description="발전된 아이디어 간 연관성과 외부 연구와의 유사성을 분석하여 '{research_goal}'의 전체 맥락을 제시한다.",
    agent=proximity_agent,
    expected_output="아이디어 상호 연관 지도 및 외부 참고자료"
)

meta_review_task = Task(
    description="최종 결과물을 종합적으로 검토하고 '{research_goal}'에 부합하는 전체 품질 향상을 위한 피드백을 제공한다.",
    agent=meta_review_agent,
    expected_output="종합 리뷰 및 개선 제안"
)

###############################################
# (E) Crew 구성 (manager_agent는 agents 리스트에서 제외)
###############################################
research_crew = Crew(
    agents=[
        generation_agent,
        reflection_agent,
        ranking_agent,
        evolution_agent,
        proximity_agent,
        meta_review_agent
    ],
    tasks=[
        supervisor_task,
        generation_task,
        reflection_task,
        ranking_task,
        evolution_task,
        proximity_task,
        meta_review_task
    ],
    process="hierarchical",            # 계층적 프로세스
    manager_agent=supervisor_agent,     # Supervisor Agent가 매니저로 지정됨
    verbose=True
)

###############################################
# (F) 실행 예시 (main 함수)
###############################################
if __name__ == "__main__":
    # 예시 입력값 (여기서 research_goal이 사용됩니다)
    inputs = {
        "research_goal": "archimedean property의 증명과 그 파생 원리의 사용"
    }

    # 전체 크루 실행
    result = research_crew.kickoff(inputs=inputs)

    # 결과 및 로그를 메모장(텍스트 파일)으로 저장
    with open("co_scientist_log.txt", "w", encoding="utf-8") as f:
        f.write("=== AI Co-Scientist Process Log ===\n\n")
        for line in conversation_log:
            f.write(line + "\n")
        f.write("\n=== Final Result ===\n")
        f.write(str(result) + "\n")

    print("\n=== Done! ===")
    print("전체 실행 로그와 최종 결과가 'co_scientist_log.txt'에 저장되었습니다.")
