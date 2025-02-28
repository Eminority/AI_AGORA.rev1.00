import time
from datetime import datetime
from crewai import Agent, Task, Crew
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import Optional
from pydantic import Field

# 환경 변수 설정
gemini_api_key = "AIzaSyDrTxu6rSKvLJLdtPN9OhNg-Pgo_HCh7WU"

if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

genai.configure(api_key=gemini_api_key)

# CrewAI Logging 설정
import logging

logger = logging.getLogger("crewai")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("crewai_output.txt", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# GeminiLLM 클래스 정의
class GeminiLLM:
    _is_custom = True  # 커스텀 LLM임을 명시

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
        response = f"[Simulated Gemini 응답: '{prompt}'에 대한 답변]"
        return response

    def call(self, prompt: str, **kwargs):
        response = self.generate(prompt)
        return {"choices": [{"message": {"content": response}}]}

    def __call__(self, prompt: str, **kwargs):
        return self.call(prompt, **kwargs)

# DebateState 모델 정의
class DebateState(BaseModel):
    topic: str
    status: dict = {"type": None, "step": 0}
    debate_log: list = []
    result: Optional[str] = Field(default=None)  # None을 명시적으로 허용

# DebateAgent 클래스 정의
class DebateAgent(Agent):
    def __init__(self, name, role, goal, backstory, llm, allow_delegation):
        super().__init__(name=name, role=role, goal=goal, backstory=backstory, llm=llm, allow_delegation=allow_delegation)

    def log(self, message):
        logger.info(f"[{self.name}] {message}")

    def run_task(self, task_description):
        self.log(f"Task started: {task_description}")
        result = f"Result of '{task_description}'"
        self.log(f"Task result: {result}")
        return result

# 각 에이전트 정의
agent_judge = DebateAgent(
    name="Judge",
    role="Moderator",
    goal="Moderate the debate",
    backstory="The judge moderates the debate and ensures a fair process.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True
)

agent_pos = DebateAgent(
    name="Affirmative Side",
    role="Presenter",
    goal="Argue in favor of the topic",
    backstory="The affirmative side presents arguments supporting the topic.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True
)

agent_neg = DebateAgent(
    name="Negative Side",
    role="Presenter",
    goal="Argue against the topic",
    backstory="The negative side presents counterarguments to the affirmative side.",
    llm=GeminiLLM(gemini_api_key),
    allow_delegation=True
)

# Task 정의
def progress_task(state):
    step = state["status"]["step"]

    if step == 1:
        # 판사 주제 설명
        agent_judge.run_task("Introduce the debate topic and invite the affirmative side.")
    elif step == 2:
        # 찬성 측 주장
        agent_pos.run_task("Present arguments in favor of the topic.")
    elif step == 3:
        # 반대 측 주장
        agent_neg.run_task("Present arguments against the topic.")
    elif step == 4:
        # 판사 변론 준비시간
        time.sleep(1)
        agent_judge.run_task("Allow time for rebuttals.")
    # 추가 단계 로직들 처리

    state["status"]["step"] += 1
    return state

def evaluate_task(state):
    # 찬성, 반대측 주장 및 반박을 추출하여 평가
    pos_log = next(log for log in state["debate_log"] if log["speaker"] == "pos")
    neg_log = next(log for log in state["debate_log"] if log["speaker"] == "neg")

    # 각 주장 평가 (예시로 간단히 점수화 작업만)
    logicality_pos = 80  # 예시 점수
    logicality_neg = 75  # 예시 점수

    state["result"] = "positive" if logicality_pos > logicality_neg else "negative"
    return state

# Crew 구성
debate_state = DebateState(
    topic="AI in Society",
    status={"type": "in_progress", "step": 1},
    debate_log=[],
    result=None
)

progress_task = Task(
    description="Manage the debate progress.",
    agent=agent_judge,
    expected_output="Updated debate state"
)

evaluate_task = Task(
    description="Evaluate the debate results.",
    agent=agent_judge,
    expected_output="Final evaluation of the debate"
)

research_crew = Crew(
    agents=[agent_judge, agent_pos, agent_neg],
    tasks=[progress_task, evaluate_task],
    process="sequential", 
    manager_agent=agent_judge,
    verbose=True
)

# Crew 실행
if __name__ == "__main__":
    state = debate_state.dict()

    # `kickoff()` 호출 시 input_data를 전달하지 않고 실행
    results = research_crew.kickoff()

    print(results)
