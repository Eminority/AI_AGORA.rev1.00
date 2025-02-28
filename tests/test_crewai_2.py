import os
from dotenv import load_dotenv
import logging
import google.generativeai as genai  # Google Gemini API 관련 라이브러리
import litellm
from crewai import Agent, Task, Crew, Process
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from typing import Any

# 전역 로그 리스트 및 발언 횟수 기록
conversation_log = []
utterance_counts = {}

def increment_utterance(agent_name: str):
    utterance_counts[agent_name] = utterance_counts.get(agent_name, 0) + 1
    logger.debug(f"Increment: {agent_name} now has {utterance_counts[agent_name]} utterances.")

def check_termination_condition() -> bool:
    if not utterance_counts:
        return False
    all_spoken = all(count >= 1 for count in utterance_counts.values())
    many_spoken = sum(1 for count in utterance_counts.values() if count >= 2)
    condition = all_spoken and many_spoken >= 3
    logger.debug(f"Termination check: all_spoken={all_spoken}, many_spoken={many_spoken} -> {condition}")
    return condition

# .env 파일에서 환경 변수 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

# Gemini API 설정 (시뮬레이션 응답 사용)
genai.configure(api_key=gemini_api_key)

# 로깅 설정: DEBUG 레벨로 설정하여 최대한 자세한 로그 출력
logger = logging.getLogger("crewai")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("crewai_output.txt", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

###############################################
# (A) Gemini 전용 커스텀 LLM 클래스 (시뮬레이션 응답)
###############################################
class GeminiLLM:
    _is_custom = True
    def __init__(self, api_key):
        self.api_key = api_key
        self._supported_params = {"temperature": True, "max_tokens": True}
        self.model_name = "gemini/gemini-2.0-flash"
    @property
    def supported_params(self):
        return self._supported_params
    def get_supported_params(self):
        return self._supported_params
    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            logger.debug("Empty prompt received in generate(), returning default response.")
            return "[Default response]"
        response = f"[Simulated Gemini 응답: '{prompt}'에 대한 답변]"
        logger.debug(f"LLM.generate() - Prompt: {prompt} / Response: {response}")
        conversation_log.append(f"LLM - {prompt} => {response}")
        return response
    def call(self, prompt: str, **kwargs):
        try:
            response = self.generate(prompt)
            if not response or response.strip() == "":
                raise ValueError("Invalid response from LLM call - None or empty.")
            return {"choices": [{"message": {"content": response}}]}
        except Exception as e:
            logger.error(f"LLM call error for prompt '{prompt}': {e}")
            conversation_log.append(f"LLM call error for prompt '{prompt}': {e}")
            return {"choices": [{"message": {"content": "[Default response]"}}]}
    def __call__(self, prompt: str, **kwargs):
        return self.call(prompt, **kwargs)

###############################################
# (B) LoggingAgent 정의 (CrewAI Agent 확장)
###############################################
class LoggingAgent(Agent):
    def __init__(self, name, role, goal, backstory, llm, allow_delegation):
        super().__init__(name=name, role=role, goal=goal, backstory=backstory, llm=llm, allow_delegation=allow_delegation)
        object.__setattr__(self, "agent_name", name)
    def log(self, message):
        full_message = f"[{self.agent_name}] {message}"
        logger.debug(full_message)
        conversation_log.append(full_message)
        with open("agent_utterances.txt", "a", encoding="utf-8") as f:
            f.write(full_message + "\n")
        increment_utterance(self.agent_name)
    def run_task(self, task_description):
        self.log(f"Task: {task_description}")
        result = f"Short result from {self.agent_name}"
        self.log(f"Result: {result}")
        return result

###############################################
# (C) 에이전트 정의 (간소화)
###############################################
supervisor_agent = LoggingAgent(
    name="King Sejong",
    role="대화 조정자",
    goal="각 agent가 최소 1회 발언하고, 두 번 이상 발언한 agent가 3명 이상이면 전체 작업 종료",
    backstory="발언은 최대한 간결하게.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
agent_disney = LoggingAgent(
    name="Walt_Disney",
    role="아이디어 정리",
    goal="연구 목표에 대해 간단 아이디어 생성",
    backstory="간결하게 답변.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
agent_buffett = LoggingAgent(
    name="Warren_Buffett",
    role="시장 분석",
    goal="간단 시장 분석 결과 제시",
    backstory="최소 발언.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
agent_gates = LoggingAgent(
    name="Bill_Gates",
    role="기술 분석",
    goal="짧은 기술 분석 결과 제시",
    backstory="간단 명료하게.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
agent_oppenheimer = LoggingAgent(
    name="Oppenheimer",
    role="리스크 평가",
    goal="짧은 위험 평가",
    backstory="최소 발언.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
agent_musk = LoggingAgent(
    name="Elon_Musk",
    role="피드백 수집",
    goal="간단 사용자 피드백",
    backstory="짧게 보고.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
agent_edison = LoggingAgent(
    name="Edison",
    role="아이디어 개선",
    goal="간단 개선안 제시",
    backstory="최소 발언.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True,
)
final_summary_agent = LoggingAgent(
    name="Summary_Agent",
    role="요약",
    goal="전체 내용을 간단히 요약하고 발언하면 전체 작업 종료",
    backstory="간결 요약 전문가.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=False,
)

###############################################
# (D) 작업(Task) 정의 (간소화된 버전)
###############################################
supervisor_task = Task(
    description=" {research_goal}을 보고 연구 목표와 agent 발언을 받아 간단히 종합 보고서를 작성한다.",
    agent=supervisor_agent,
    expected_output="종합 보고서"
)
classifier_task = Task(
    description="{research_goal}을 보고 간단 아이디어 생성",
    agent=agent_disney,
    expected_output="아이디어 리스트"
)
market_task = Task(
    description="{research_goal}을 보고 간단 시장 분석 제시",
    agent=agent_buffett,
    expected_output="시장 분석 결과"
)
technical_task = Task(
    description="{research_goal}을 보고 간단 기술 분석 제시",
    agent=agent_gates,
    expected_output="기술 분석 결과"
)
risk_task = Task(
    description="{research_goal}을 보고 간단 위험 평가 제시",
    agent=agent_oppenheimer,
    expected_output="위험 평가 결과"
)
final_summary_task = Task(
    description="전체 agent 발언과 결과를 간단히 요약",
    agent=final_summary_agent,
    expected_output="최종 요약 보고서"
)

###############################################
# (E) Crew 구성 (간소화)
###############################################
research_crew = Crew(
    agents=[
        agent_buffett,
        agent_disney,
        agent_gates,
        agent_oppenheimer,
        final_summary_agent
    ],
    tasks=[
        supervisor_task,
        classifier_task,
        market_task,
        technical_task,
        risk_task,
        final_summary_task
    ],
    process="sequential",
    manager_agent=supervisor_agent,
    verbose=True
)

###############################################
# (F) LangGraph 정적 워크플로우 구성 및 실행
###############################################
class CrewState(BaseModel):
    research_goal: str
    results: dict = {}

initial_state = CrewState(
    research_goal="""CrewAI를 사용한 Multi AI Agent 시스템 구현 아이디어
    1. 데이터 수집 최소화.
    2. TASK 간소화.
    3. 전체 결과 간단 요약.
    """,
    results={}
)

graph = StateGraph(state_schema=CrewState)
graph.state = initial_state

def execute_crewai(state: CrewState) -> CrewState:
    input_data = {"research_goal": state.research_goal}
    # 각 Task의 description에 research_goal을 주입
    for task in research_crew.tasks:
        formatted = task.description.format(**input_data)
        task.description = formatted
        conversation_log.append(f"[Debug] Formatted Task for {task.agent.dict().get('name','unknown')}: {formatted}")
    logger.debug(f"Input data for CrewAI: {input_data}")
    conversation_log.append(f"[Debug] Input data: {input_data}")
    results = research_crew.kickoff(input_data)
    conversation_log.append(f"[Debug] CrewAI 결과: {results}")
    state.results = results
    if final_summary_agent.agent_name in results:
        conversation_log.append("[Supervisor] 최종 요약 태스크 실행됨. 작업 종료.")
    return state

graph.add_node("execute_crewai", execute_crewai)
graph.add_edge(START, "execute_crewai")
graph.add_edge("execute_crewai", END)

compiled = graph.compile()
try:
    final_state = compiled.invoke(initial_state.dict())
except Exception as e:
    logger.error(f"그래프 실행 중 오류 발생: {e}")
    conversation_log.append(f"[Error] 그래프 실행 중 오류 발생: {e}")
    final_state = initial_state
finally:
    try:
        final_state_dict = final_state.dict() if hasattr(final_state, "dict") else final_state
    except Exception as e:
        logger.error(f"최종 상태 dict 변환 오류: {e}")
        conversation_log.append(f"[Error] 최종 상태 dict 변환 오류: {e}")
        final_state_dict = {}
    results = final_state_dict.get("results", {})
    if hasattr(results, "dict"):
        results = results.dict()
    
    final_summary_agent_name = final_summary_agent.agent_name
    task_output: Any = results.get(final_summary_agent_name, "No Task Output")
    crew_output: Any = final_state_dict.get("output", "No Crew Output")
    
    final_report = "\n".join([f"{agent_name}: {result}" for agent_name, result in results.items()])
    supervisor_agent.log("최종 보고서 작성 완료")
    supervisor_agent.log("\n" + final_report)
    
    try:
        with open("multi_agent_log.txt", "w", encoding="utf-8") as f:
            f.write("=== AI Co-Scientist Process Log ===\n\n")
            for line in conversation_log:
                f.write(line + "\n")
            f.write("\n=== Final Report ===\n")
            f.write(final_report + "\n")
            f.write("\n=== Task Output ===\n")
            f.write(str(task_output) + "\n")
            f.write("\n=== Crew Output ===\n")
            f.write(str(crew_output) + "\n")
    except Exception as e:
        logger.error(f"파일 저장 중 오류 발생: {e}")
        conversation_log.append(f"[Error] 파일 저장 중 오류 발생: {e}")
    
    print("\n=== Done! ===")
    print("전체 실행 로그와 최종 결과가 'multi_agent_log.txt'에 저장되었습니다.")
