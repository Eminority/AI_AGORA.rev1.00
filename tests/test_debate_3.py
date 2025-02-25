import os
import json
from dotenv import load_dotenv
from langchain.memory import ConversationSummaryBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnableSequence
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.exceptions import OutputParserException

# ✅ 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ LangChain 모델 설정
pos_agent = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=120)
neg_agent = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=120)
progress_agent = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=120)
next_speaker_agent = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=120)
judge_agent = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, request_timeout=120)

# ✅ Output Parser 설정
response_schemas = [
    ResponseSchema(name="speaker", description="The speaker of the response (Pos, Neg, Judge)"),
    ResponseSchema(name="message", description="The content of the response")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# ✅ Memory 설정
pos_memory = ConversationSummaryBufferMemory(llm=pos_agent, memory_key="pos_history", input_key="input", return_messages=True)
neg_memory = ConversationSummaryBufferMemory(llm=neg_agent, memory_key="neg_history", input_key="input", return_messages=True)
progress_memory = ConversationSummaryBufferMemory(llm=progress_agent, memory_key="progress_history", input_key="input", return_messages=True)
next_speaker_memory = ConversationSummaryBufferMemory(llm=next_speaker_agent, memory_key="next_speaker_history", input_key="input", return_messages=True)

# ✅ 발언 순서 결정 AI 프롬프트 (JSON 형식 강제)
next_speaker_prompt = PromptTemplate(
    input_variables=["history"],
    template="""
    🔹 지금까지의 토론 내용:
    {history}

    다음 발언자를 결정하세요. 반드시 JSON 형식으로 반환하세요:
    ```json
    {{
        "speaker": "Pos" 또는 "Neg",
        "message": "Next speaker is Pos/Neg."
    }}
    ```
    **Judge는 첫 발언자가 될 수 없습니다.**
    **동일한 측이 연속으로 발언할 수 없습니다.**

    **Pos, Neg는 최소한 두 번씩은 발언을 해야합니다. {history}를 참조하여 발언자가 두 번 이상 발언했는지 확인하시오.**
    """
)

# ✅ 진행자 프롬프트 (유저에게 표시)
progress_prompt = PromptTemplate(
    input_variables=["speaker", "message"],
    template="""
    🔹 [진행 상황] {speaker}: {message}
    """
)

# ✅ 토론자 프롬프트 (자연어 응답)
argument_prompt = PromptTemplate(
    input_variables=["topic", "position", "opponent_statements"],
    template="""
    당신은 "{topic}"에 대한 토론을 진행하고 있습니다.
    당신의 입장은 **{position}**입니다.

    📌 상대 측의 주장:
    {opponent_statements}

    논리적인 근거와 예시를 들어 반박하세요.
    반드시 JSON 형식으로 응답하세요:
    ```json
    {{
        "speaker": "{position}",
        "message": "..."
    }}
    ```
    """
)

# ✅ Judge 프롬프트
judge_prompt = PromptTemplate(
    input_variables=["topic", "pos_statements", "neg_statements"],
    template="""
    당신은 "{topic}"에 대한 토론의 판결을 내리는 심판입니다.

    **찬성 측 (Pos)의 주장:**
    {pos_statements}

    **반대 측 (Neg)의 주장:**
    {neg_statements}

    어느 쪽이 더 논리적이고 설득력 있는지를 평가하세요. 어느 한쪽을 반드시 선택해야 합니다.
    선택한 쪽이 왜 더 논리적이고 설득력 있는지에 대한 이유도 서술하세요.
    반드시 JSON 형식으로 응답하세요:
    ```json
    {{
        "speaker": "Judge",
        "message": "더 논리적인 사람은 Pos/Neg입니다. 그 이유는 입니다."
    }}
    ```
    """
)

def print_progress(result):
    """ 🔹 진행 상황을 즉시 출력하는 함수 """
    speaker = result.get("speaker", "Unknown")
    message = result.get("message", "No message received.")
    print(f"\n🔹 [{speaker}] {message}\n")
    return result

class Debate:
    def __init__(self, topic: str):
        self.topic = topic
        self.memory = {
            "pos": pos_memory,
            "neg": neg_memory,
            "progress": progress_memory,
            "next_speaker": next_speaker_memory
        }
        self.progress_chain = RunnableSequence(
            RunnableLambda(self.next_speaker),
            RunnableLambda(print_progress),
            RunnableLambda(self.debate_turn),
            RunnableLambda(print_progress),
            RunnableLambda(self.next_speaker),
            RunnableLambda(print_progress),
            RunnableLambda(self.debate_turn),
            RunnableLambda(print_progress),
            RunnableLambda(self.next_speaker),
            RunnableLambda(print_progress),
            RunnableLambda(self.debate_turn),
            RunnableLambda(print_progress),
            RunnableLambda(self.next_speaker),
            RunnableLambda(print_progress),
            RunnableLambda(self.debate_turn),
            RunnableLambda(print_progress),
            RunnableLambda(self.evaluate),
            RunnableLambda(print_progress)
        )

    def start(self):
        return self.progress_chain.invoke({})

    def next_speaker(self, _):
        """ ✅ 발언 순서를 결정하는 함수 (Memory 활용) """
        history = self.memory["next_speaker"].load_memory_variables({})

        # ✅ history가 HumanMessage 객체라면 string 변환
        history_str = "\n".join([msg.content for msg in history.get("next_speaker_history", [])]) if history else ""

        result = next_speaker_agent.invoke(next_speaker_prompt.format(history=history_str))

        try:
            parsed_result = output_parser.parse(result.content)
            next_speaker = parsed_result["speaker"]
            message = parsed_result["message"]

            # ✅ next_speaker가 올바르게 지정되었는지 검토
            if next_speaker not in ["Pos", "Neg"]:
                next_speaker = "Neg" if history.get("last_speaker") == "Pos" else "Pos"

        except OutputParserException:
            print(f"⚠️ JSON Parsing Error in next_speaker():\n{result.content}")
            next_speaker = "Neg" if history.get("last_speaker") == "Pos" else "Pos"
            message = f"Defaulting to {next_speaker}."

        self.memory["next_speaker"].save_context({"input": history_str}, {"message": message})
        return {"speaker": next_speaker, "message": message}

    def debate_turn(self, speaker_result):
        """ ✅ 찬성/반대 측이 주장/반론을 수행하는 함수 """
        speaker = speaker_result["speaker"]
        opponent = "Neg" if speaker == "Pos" else "Pos"
        opponent_statements = self.memory[opponent.lower()].load_memory_variables({})

        prompt = argument_prompt.format(topic=self.topic, position=speaker, opponent_statements=opponent_statements)
        result = pos_agent.invoke(prompt) if speaker == "Pos" else neg_agent.invoke(prompt)

        parsed_result = output_parser.parse(result.content)
        self.memory[speaker.lower()].save_context({"input": prompt}, {"message": parsed_result["message"]})

        return parsed_result

    def evaluate(self, _):
        """ ✅ 판결 AI가 최종 승패를 결정하는 함수 """
        pos_statements = self.memory["pos"].load_memory_variables({})
        neg_statements = self.memory["neg"].load_memory_variables({})
        result = judge_agent.invoke(judge_prompt.format(topic=self.topic, pos_statements=pos_statements, neg_statements=neg_statements))

        parsed_result = output_parser.parse(result.content)
        return parsed_result
