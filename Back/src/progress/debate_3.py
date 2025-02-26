import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.exceptions import OutputParserException
from langchain.schema import SystemMessage, HumanMessage
from .progress import Progress

class DebateMemoryManager:
    def __init__(self):
        self.history = []
        self.current_round = 1

    def save_message(self, speaker: str, message: str, round_number: int = None):
        if round_number is None:
            round_number = self.current_round
        self.history.append({
            "round": round_number,
            "speaker": speaker,
            "message": message
        })

    def load_all(self):
        return self.history

    def load_by_speaker(self, speaker: str):
        return [msg for msg in self.history if msg["speaker"] == speaker]

    def get_last_message(self, speaker: str):
        msgs = self.load_by_speaker(speaker)
        if msgs:
            return msgs[-1]["message"]
        return None

    def increment_round(self):
        self.current_round += 1

    def format_history(self):
        return "\n".join([f"[Round {msg['round']}] {msg['speaker']}: {msg['message']}" for msg in self.history])

class Debate(Progress):
    def __init__(self, participant:dict, generate_text_config:dict, data:dict=None):
        # participant:{"judge": Participant, "pos": Participant, "neg": Participant} 형태.
        super().__init__(participant=participant,
                         generate_text_config=generate_text_config,
                         data=data)

        self.data = data
        if self.data == None:
            # debate 필드 초기화
            self.data = {
                "participants": None,
                "topic": None,
                "status": {
                    "type": None,  # "in_progress" 또는 "end" 등
                    "step": 0     # 1부터 11까지 단계
                },
                "debate_log": [],
                "start_time": None,
                "end_time": None,
                "summary": {
                    "summary_pos": None,
                    "summary_neg": None,
                    "summary_arguments": None,
                    "summary_verdict": None
                },
                "result": None
            }


        # Output Parser 설정
        response_schemas = [
            ResponseSchema(name="speaker", description="The speaker of the response (Pos, Neg, Judge)"),
            ResponseSchema(name="message", description="The content of the response")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

        # 프롬프트 템플릿 구성

        # 후보 리스트를 포함한 next_speaker 프롬프트
        self.next_speaker_candidate_prompt = PromptTemplate(
            input_variables=["history", "candidates"],
            template="""
            🔹 지금까지의 토론 내용:
            {history}

            다음 발언자로 적합한 후보는 다음과 같습니다: {candidates}.
            토론 상황을 고려하여, 가장 적합한 발언자를 하나 선택하고, JSON 형식으로 반환하세요:
            ```json
            {{
                "speaker": "<선택한 후보>",
                "message": "다음 발언자로 <선택한 후보>가 적합합니다."
            }}
            ```
            """
        )

        # claim 프롬프트 (Round 1 주장의 경우)
        self.claim_prompt = PromptTemplate(
            input_variables=["topic", "position"],
            template="""
            [SYSTEM: 당신은 토론 참가자입니다. 역할은 자신의 주장을 처음으로 제시하는 것입니다.]
            당신은 "{topic}"에 대한 토론에 참여하고 있습니다.
            이번 라운드에서는 자신의 주장을 처음으로 제시해 주세요.
            당신의 입장은 **{position}**입니다.
            주요 근거와 함께 자신의 주장을 명확하게 기술해 주세요.
            반드시 JSON 형식으로 응답하세요:
            ```json
            {{
                "speaker": "{position}",
                "message": "..."
            }}
            ```
            """
        )

        # argument 프롬프트 (Round 2 이후 반박)
        self.argument_prompt = PromptTemplate(
            input_variables=["topic", "position", "opponent_statements"],
            template="""
            [SYSTEM: 당신은 토론 참가자입니다. 역할은 상대의 주장을 반박하는 것입니다.]
            당신은 "{topic}" 토론에 참여하고 있습니다.
            당신의 입장은 **{position}**입니다.
            상대 측의 주장:
            {opponent_statements}
            위 내용을 바탕으로 논리적인 근거와 예시를 들어 반박해 주세요.
            반드시 JSON 형식으로 응답하세요:
            ```json
            {{
                "speaker": "{position}",
                "message": "..."
            }}
            ```
            """
        )

        # evaluator 프롬프트 (라운드별 평가; 논리력, 신선도, 사실 기반)
        self.evaluator_prompt = PromptTemplate(
            input_variables=["history"],
            template="""
            [SYSTEM: 당신은 토론 심판입니다. 역할은 라운드 평가를 진행하는 것입니다.]
            다음은 이번 라운드의 토론 발언 기록입니다:
            {history}

            각 참가자(찬성 측: "Pos", 반대 측: "Neg")의 발언을 아래 기준으로 평가해 주세요.
            1. 논리력 (Logical Validity) (0~10점)
            2. 신선도 (Freshness) (0~10점)
            3. 사실 기반 (Factuality) (0~10점)

            평가 결과는 반드시 JSON 형식으로 반환하세요. 예시:
            {{
                "evaluations": [
                    {{"participant": "Pos", "logic_score": 8, "freshness_score": 6, "factuality_score": 9, "warning": ""}},
                    {{"participant": "Neg", "logic_score": 7, "freshness_score": 5, "factuality_score": 8, "warning": "발언이 반복적입니다."}}
                ],
                "message": "라운드 평가 결과입니다."
            }}
            """
        )

        # judge_prompt (최종 판결 프롬프트)
        self.judge_prompt = PromptTemplate(
            input_variables=["topic", "pos_statements", "neg_statements"],
            template="""
            [SYSTEM: 당신은 토론 심판입니다. 역할은 최종 판결을 내리는 것입니다.]
            당신은 "{topic}" 토론의 최종 판결을 내려야 합니다.
            아래는 찬성 측(Pos)과 반대 측(Neg)의 발언 내역입니다:
            
            **찬성 측 (Pos):**
            {pos_statements}
            
            **반대 측 (Neg):**
            {neg_statements}
            
            이제 어느 쪽이 더 설득력이 있는지, 그리고 그 이유는 무엇인지 상세하게 서술해 주세요.
            반드시 JSON 형식으로 응답하세요:
            ```json
            {{
               "speaker": "Judge",
               "message": "최종 판결: [Pos/Neg]가 더 설득력이 있습니다. 이유: ..."
            }}
            ```
            """
        )

        # progress_agent 프롬프트: Round 1 라운드 안내
        self.progress_round1_prompt = PromptTemplate(
            input_variables=["topic"],
            template="""
            [SYSTEM: 당신은 토론 진행자입니다. 역할은 라운드 안내 및 다음 발언자 소개입니다. 참가자로서 발언하지 마십시오.]
            Round 1 시작:
            이번 토론의 주제는 "{topic}" 입니다.
            각 참가자께서는 자신의 주장을 처음으로 제시해 주시기 바랍니다.
            """
        )

        # progress_agent 프롬프트: 이후 라운드 안내 (이전 라운드 평가 결과와 남은 발언 시간 안내)
        self.progress_round_prompt = PromptTemplate(
            input_variables=["evaluation", "pos_time", "neg_time"],
            template="""
            [SYSTEM: 당신은 토론 진행자입니다. 역할은 이전 라운드 평가 결과와 남은 발언 시간을 전달하는 것입니다. 참가자로서 발언하지 마십시오.]
            이번 라운드의 평가 결과는 다음과 같습니다:
            {evaluation}
            남은 발언 시간: 찬성 측 {pos_time:.2f}초, 반대 측 {neg_time:.2f}초.
            """
        )

        # progress_agent 프롬프트: 단순 진행 내역 안내용 (발언 시간 결정과 관련 없이 사용)
        self.progress_prompt = PromptTemplate(
            input_variables=["history"],
            template="""
            [SYSTEM: 당신은 토론 진행자입니다. 역할은 단순히 토론 내역을 확인하는 것입니다. 참가자로서 발언하지 마십시오.]
            지금까지의 토론 기록:
            {history}
            """
        )

        self.memory_manager = DebateMemoryManager()

    def _print_progress(self, results: dict) -> dict:
        speaker = results.get("speaker", "Unknown")
        message = results.get("message", "No message received.")
        print(f"\n🔹 [{speaker}] {message}\n")
        return results

    def next_speaker(self, is_final: bool = False) -> dict:
        history_str = self.memory_manager.format_history()
        if is_final:
            candidates = "['Judge']"
        else:
            candidates = "['Pos', 'Neg']"
        system_msg = SystemMessage(content="당신은 토론 진행자입니다. 역할은 다음 발언자를 결정하는 것입니다.")
        human_msg = HumanMessage(content=self.next_speaker_candidate_prompt.format(history=history_str, candidates=candidates))
        results = self.next_speaker_agent.invoke([system_msg, human_msg])
        try:
            parsed_result = self.output_parser.parse(results.content)
            next_speaker = parsed_result["speaker"]
            message = parsed_result["message"]
            if is_final and next_speaker != "Judge":
                next_speaker = "Judge"
                message = "최종 판결을 위해 Judge가 선택되었습니다."
            elif not is_final and next_speaker not in ["Pos", "Neg"]:
                next_speaker = "Neg"
        except OutputParserException:
            next_speaker = "Neg" if not is_final else "Judge"
            message = f"Defaulting to {next_speaker}."
        self.memory_manager.save_message("System", f"Next speaker decided: {next_speaker}. {message}")
        return {"speaker": next_speaker, "message": message}

    def debate_turn(self, speaker: str, round_number: int) -> dict:
        if round_number == 1:
            prompt = self.claim_prompt.format(topic=self.topic, position=speaker)
        else:
            opponent = "Neg" if speaker == "Pos" else "Pos"
            opponent_msgs = self.memory_manager.load_by_speaker(opponent)
            opponent_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in opponent_msgs])
            prompt = self.argument_prompt.format(topic=self.topic, position=speaker, opponent_statements=opponent_statements)
        if speaker == "Pos":
            system_msg = SystemMessage(content="당신은 찬성 측 토론 참가자입니다. 자신의 주장을 제시하세요.")
            human_msg = HumanMessage(content=prompt)
            results = self.pos_agent.invoke([system_msg, human_msg])
        elif speaker == "Neg":
            system_msg = SystemMessage(content="당신은 반대 측 토론 참가자입니다. 자신의 주장을 제시하세요.")
            human_msg = HumanMessage(content=prompt)
            results = self.neg_agent.invoke([system_msg, human_msg])
        else:
            system_msg = SystemMessage(content="당신은 심판입니다. 최종 판결을 내리세요.")
            human_msg = HumanMessage(content=prompt)
            results = self.judge.invoke([system_msg, human_msg])
        parsed_result = self.output_parser.parse(results.content)
        message = parsed_result["message"]
        self.memory_manager.save_message(speaker, message)
        return {"speaker": speaker, "message": message}

    def decide_continue(self, round_number: int) -> bool:
        # 라운드별 평가를 진행하지만 최종 토론 종료 조건은 발언 시간에 따름
        history_str = self.memory_manager.format_history()
        system_msg_eval = SystemMessage(content="당신은 심판입니다. 이번 라운드의 평가를 진행하세요.")
        human_msg_eval = HumanMessage(content=self.evaluator_prompt.format(history=history_str))
        eval_result = self.judge.invoke([system_msg_eval, human_msg_eval])
        try:
            eval_json = json.loads(eval_result.content)
            self.memory_manager.save_message("Evaluator", f"Round evaluation: {json.dumps(eval_json, ensure_ascii=False)}")
            print("\n[DEBUG] Evaluator JSON:", json.dumps(eval_json, ensure_ascii=False))
            self._print_progress({"speaker": "Evaluator", "message": json.dumps(eval_json, ensure_ascii=False)})
        except Exception as e:
            print("\n[DEBUG] Evaluator parsing error:", e)
            self.memory_manager.save_message("Evaluator", "Round evaluation parsing failed.")
            eval_json = {}
        # 이 함수는 발언 시간이 종료되었는지를 판단하는 용도로는 사용하지 않음.
        return True

    def evaluate(self, _) -> dict:
        # 최종 판결: judge_prompt 사용
        pos_msgs = self.memory_manager.load_by_speaker("Pos")
        neg_msgs = self.memory_manager.load_by_speaker("Neg")
        pos_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in pos_msgs])
        neg_statements = "\n".join([f"[Round {msg['round']}] {msg['message']}" for msg in neg_msgs])
        prompt = self.judge_prompt.format(topic=self.topic, pos_statements=pos_statements, neg_statements=neg_statements)
        system_msg = SystemMessage(content="당신은 심판입니다. 최종 판결을 내리세요.")
        human_msg = HumanMessage(content=prompt)
        results = self.judge.invoke([system_msg, human_msg])
        parsed_result = self.output_parser.parse(results.content)
        self.memory_manager.save_message("Judge", parsed_result["message"])
        return {"speaker": "Judge", "message": parsed_result["message"]}

    def progress(self) -> dict:
        debate = self.data
        result = {"timestamp" : None, "speaker" : "", "message" : ""}

        # 유효하지 않은 토론이면 메시지 반환
        if debate["_id"] is None:
            result["speaker"] = "SYSTEM"
            result["message"] = "유효하지 않은 토론입니다."
            result["timestamp"] = datetime.now()
            return result
        
        
        # 각 참가자에게 주어진 발언 시간(초)
        pos_time_remaining = 20.0
        neg_time_remaining = 20.0

        # 초기 발언자 결정 (일반 라운드에서는 Pos/Neg)
        initial = self.next_speaker(is_final=False)
        self._print_progress(initial)
        first_speaker = initial["speaker"]
        second_speaker = "Neg" if first_speaker == "Pos" else "Pos"
        order = [first_speaker, second_speaker]

        round_number = 1
        while True:
            print(f"=== Round {round_number} 시작 ===")
            # 라운드 시작 안내: progress_agent가 안내 (평가 결과 및 남은 시간 안내)
            if round_number == 1:
                system_msg = SystemMessage(content="당신은 토론 진행자입니다. 역할은 라운드 안내입니다. 참가자로서 발언하지 마십시오.")
                human_msg = HumanMessage(content=self.progress_round1_prompt.format(topic=self.topic))
                progress_msg = self.progress_agent.invoke([system_msg, human_msg]).content
            else:
                history_str = self.memory_manager.format_history()
                system_msg = SystemMessage(content="당신은 토론 진행자입니다. 역할은 이전 라운드 평가 결과와 남은 발언 시간을 전달하는 것입니다. 참가자로서 발언하지 마십시오.")
                human_msg = HumanMessage(content=self.progress_round_prompt.format(evaluation="이전 라운드 평가 참고", 
                                                                                   pos_time=pos_time_remaining, 
                                                                                   neg_time=neg_time_remaining))
                progress_msg = self.progress_agent.invoke([system_msg, human_msg]).content
            self._print_progress({"speaker": "Progress", "message": progress_msg})

            # 각 참가자 발언 및 시간 측정
            for speaker in order:
                start_time = time.time()
                turn_result = self.debate_turn(speaker, round_number)
                end_time = time.time()
                duration = end_time - start_time
                self._print_progress(turn_result)
                if speaker == "Pos":
                    pos_time_remaining -= duration
                    print(f"[DEBUG] Pos remaining time: {pos_time_remaining:.2f} seconds")
                elif speaker == "Neg":
                    neg_time_remaining -= duration
                    print(f"[DEBUG] Neg remaining time: {neg_time_remaining:.2f} seconds")
            # 발언 시간이 모두 소진되면 종료
            if pos_time_remaining <= 0 or neg_time_remaining <= 0:
                print("발언 시간이 모두 소진되어 토론을 종료합니다.")
                final_speaker = self.next_speaker(is_final=True)
                self._print_progress(final_speaker)
                break

            round_number += 1
            self.memory_manager.increment_round()

        final_eval = self.evaluate({})
        self._print_progress(final_eval)
        return final_eval
