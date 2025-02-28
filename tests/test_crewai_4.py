import os
import json
from dotenv import load_dotenv
import logging
import google.generativeai as genai  # Gemini API 관련 라이브러리
from crewai import Agent, Task, Crew, Process, LLM
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, PrivateAttr 
from typing import Any, Tuple, Union, Dict
from crewai.project import CrewBase, agent, crew, task#yaml에서 agent 가져오는 라이브러리
from crewai_tools import SerperDevTool
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

llm = LLM(
    model = "gemini/gemini-1.5-flash",
    temperature=1,
    timeout = 60,
    max_tokens = 500,
    api_key = gemini_api_key
)

class Format(BaseModel):
    speaker : str
    message : str

@CrewBase
class Create():
    agents_config = "agents.yaml"
    tasks_config = "task.yaml"
    

    @agent
    def agent_buffett(self) -> Agent:
        return Agent(
            config = self.agents_config['agent_buffett'],
            verbose = True,
            max_execution_time = 120, 
            allow_delegation = False, 
            llm = llm
        )
    @agent
    def agent_gates(self) -> Agent:
        return Agent(
            config = self.agents_config['agent_gates'],
            verbose = True,
            max_execution_time = 120, 
            allow_delegation = False, 
            llm = llm
        )
    @agent
    def agent_edison(self) -> Agent:
        return Agent(
            config = self.agents_config['agent_edison'],
            verbose = True,
            max_execution_time = 120, 
            allow_delegation = False, 
            llm = llm
        )
    @agent
    def agent_sejong(self) -> Agent:
        return Agent(
            config = self.agents_config['agent_sejong'],
            verbose = True,
            max_execution_time = 120, 
            allow_delegation = False, 
            llm = llm
        )


    @task
    def supervisor_task(self) -> Task:
        return Task(
            config=self.tasks_config['supervisor_task'],
            async_execution= False, #비동기 실행. 기본값 False
            agent = self.agent_sejong(), 
            human_input=False, #작업이 에이전트의 최종 답변을 인간 검토해야하는지 여부. 기본값 False
            output=None, #출력 파일 경로. 기본값 None
            output_json=Format, #[Type[BaseModel]] Json 출력을 구조화하기 위한 Pydantic 모델
            callback=None, #작업 완료 후 실행할 함수/객체
            
        )
    @task   
    def market_task(self) -> Task:
        return Task(
            config=self.tasks_config['market_task'],
            async_execution= False, 
            agent = self.agent_buffett(), 
            human_input=False, 
            output=None, 
            output_json=Format, 
            callback=None, 

        )
    @task
    def technical_task(self) -> Task:
        return Task(
            config=self.tasks_config['technical_task'],
            async_execution= False, 
            agent = self.agent_gates(), 
            human_input=False, 
            output=None, 
            output_json=Format, 
            callback=None, 
        )
    @task
    def improvement_task(self) -> Task:
        return Task(
            config=self.tasks_config['improvement_task'],
            async_execution= False, 
            agent = self.agent_edison(), 
            human_input=False, 
            output=None, 
            output_json=Format, 
            callback=None, 
        )
    # task_output= task.output


    # print(f"Task Description : {task_output.description}")
    # print(f"Task Summary : {task_output.summary}")
    # print(f"Raw Output : {task_output.raw}")
    # if task_output.json_dict :
    #      print(f"JSON Output: {json.dumps(task_output.json_dict, indent=2)}")

    @crew
    def crew(self) -> Crew:
        return Crew(
        agents=[
            self.agent_buffett(),
            self.agent_gates(),
            self.agent_edison(),
            self.agent_sejong(),
        ],
        tasks=[
            self.supervisor_task(),
            self.market_task(),
            self.technical_task(),
            self.improvement_task()
        ],
        process=Process.sequential,
        verbose = True, #실행중 로깅 기본값 False
        manager_llm=llm, #관리자 agent가 사용하는 모델 (계층적 프로세스 사용시 필요)
        # task_callback= print(self.task_output.raw),
        output_log_file=True,
        )

    # def callback_function(output : task_output):
    #     print(f"""
    #           Task complete
    #           Task : {output.description})
    #           Output : {output.raw}
    #     """)


    # save_output_task = Task(
    #     description='Save the summarized AI news to a file',
    #     expected_output='File saved successfully',
    #     agent=self.supervisior_agent,
    #     tools=[file_save_tool],
    #     output_file='outputs/ai_news_summary.txt',
    #     create_directory=True
    # )
# Task_Create 클래스의 인스턴스 생성
task_create_instance = Create()

# crew 메서드를 호출하여 Crew 객체를 가져옴
crew_instance = task_create_instance.crew()
inputs = {'topic' : 'CrewAI를 사용한 Multi ai agent 기술 구현'}
result = crew_instance.kickoff(inputs)
print(result)