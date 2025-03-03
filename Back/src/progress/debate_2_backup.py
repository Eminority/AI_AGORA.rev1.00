import time
from datetime import datetime
from .progress import Progress
import re

class Debate_2(Progress):
    """
    debate를 관리하는 클래스
    self.participants에 judge, pos, neg ai를 넣넣는다.
    self.data에 save할 데이터를 넣는다.
    generate_text_config에는 max_tokens, k, temperature 값을 저장한다.
    method : progress
    method : evaluate
    """
    def __init__(self, participant:dict, generate_text_config:dict, data:dict=None, ):
        # participant:{"judge": Participant, "pos": Participant, "neg": Participant} 형태.
        super().__init__(participant=participant,
                         generate_text_config=generate_text_config,
                         data=data)

        # 총 11단계 진행
        self.max_step = 11

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


    def progress(self) -> dict:
        """
        11단계 순서:
        1) 판사가 주제 설명
        2) 찬성측 주장
        3) 반대측 주장
        4) 판사가 변론 준비시간(1초) 부여
        5) 반대측 변론
        6) 찬성측 변론
        7) 판사가 최종 주장 시간(1초) 부여
        8) 찬성측 최종 결론
        9) 반대측 최종 결론
        10) 판사가 판결 준비시간(1초) 부여
        11) 판사 최종 결론 (evaluate)
        """
        debate = self.data
        result = {"timestamp": None, "speaker": "", "message": "", "step": debate["status"]["step"]}

        # 유효하지 않은 토론이면 메시지 반환
        if debate["_id"] is None:
            result["speaker"] = "SYSTEM"
            result["message"] = "유효하지 않은 토론입니다."
            result["timestamp"] = datetime.now()
            return result

        # 단계(step)가 설정되어 있지 않다면 1로 초기화
        if "step" not in debate["status"]:
            debate["status"]["step"] = 1
        step = debate["status"]["step"]

        # 단계별 로직
        if step == 1:
            # 1. 판사가 주제 설명
            # self.ready_to_debate() -> crawling하는 단계가 필요함.
            result["speaker"] = "judge_1"
            prompt =f"""
                당신은 **"{self.data['topic']}"** 주제에 대한 토론을 진행하는 역할을 맡았습니다. 중립적인 태도로 토론을 소개하며, 주제에 대한 간략하고 객관적인 소개를 제공해야 합니다. 특정 입장을 지지하거나 반대하는 표현을 사용하지 않도록 유의하세요.  

                ### **진행 방식:**
                - **주제를 간결하고 객관적으로 요약**하세요.
                - 개인적인 의견을 배제하고 중립적인 태도를 유지하세요.
                - 주제 소개 후, **찬성 측(affirmative side)이 먼저 주장을 펼칠 수 있도록 유도**하세요.

                ---

                ### **예시 구조**:

                **소개:**  
                "'{self.data['topic']}'는 다양한 시각에서 논의되는 주제입니다. 찬성하는 측에서는 [찬성 측의 주요 주장]을 근거로 주장하며, 반대하는 측에서는 [반대 측의 주요 주장]을 내세웁니다. 이 논쟁은 주로 [토론에서 중요한 2~3가지 핵심 쟁점]을 중심으로 진행됩니다. 오늘 우리는 이 주제에 대한 양측의 입장을 깊이 탐구해보겠습니다."

                **찬성 측의 발언 유도:**  
                "그럼 먼저, **찬성 측**의 의견을 들어보겠습니다. {self.data['topic']}에 대한 찬성 입장은 무엇이며, 이를 뒷받침하는 주요 근거와 증거는 무엇인가요?"
                """
            
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 2:
            # 2. 찬성 측 주장
            result["speaker"] = "pos"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 이 주장에 찬성하는 입장에서 논증하는 것입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 주제에 대한 **찬성 입장을 명확하게 제시**하세요.  
            - 찬성하는 이유를 뒷받침할 **세 가지 이상의 강력한 논거**를 제시하세요.  
            - **논리적 근거, 현실 사례, 데이터** 등을 활용하여 주장을 강화하세요.  
            - 주제에 대한 일반적인 설명은 피하고, 오직 찬성하는 입장을 옹호하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            1. **주요 논거 #1**  
            - 설명  
            - 근거 또는 예시  

            2. **주요 논거 #2**  
            - 설명  
            - 근거 또는 예시  

            3. **주요 논거 #3**  
            - 설명  
            - 근거 또는 예시  

            간결하면서도 설득력 있게 작성하세요. 적용 가능한 경우, 사실적 근거를 제공하세요.
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"], prompt)

        elif step == 3:
            # 3. 반대 측 주장
            result["speaker"] = "neg"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 이 주장에 반대하는 입장에서 논증하는 것입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 주제에 대한 **반대 입장을 명확하게 제시**하세요.  
            - 반대하는 이유를 뒷받침할 **세 가지 이상의 강력한 논거**를 제시하세요.  
            - **논리적 근거, 현실 사례, 데이터** 등을 활용하여 주장을 강화하세요.  
            - 주제에 대한 일반적인 설명은 피하고, 오직 반대하는 입장을 옹호하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            1. **반박 논거 #1**  
            - 설명  
            - 근거 또는 예시  

            2. **반박 논거 #2**  
            - 설명  
            - 근거 또는 예시  

            3. **반박 논거 #3**  
            - 설명  
            - 근거 또는 예시  

            간결하면서도 설득력 있게 작성하세요. 적용 가능한 경우, 사실적 근거를 제공하세요.
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"], prompt)

        elif step == 4:
            # 4. 판사가 변론 준비시간 1초 제공
            result["speaker"] = "judge_1"
            result["message"] ="양측이 초기 주장을 제시하였습니다. 반론을 준비할 시간을 가지세요."

            time.sleep(1)

        elif step == 5:
            # 5. 반대 측 변론
            result["speaker"] = "neg"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **반대 측 입장에서 찬성 측(affirmative)의 주장에 반박하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - **가장 최근의 찬성 측 주장**을 검토하고 이에 대한 **논리적인 반박**을 제시하세요.  
            - 찬성 측의 **핵심 논점을 직접적으로 반박**하세요.  
            - **근거, 논리적 추론, 현실 사례**를 활용하여 상대 주장을 논파하세요.  
            - 새로운 반대 논거를 도입하지 말고, 오직 상대방의 주장을 반박하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            "찬성 측의 주장을 면밀히 검토해 보았지만, 다음과 같은 이유로 반박하고자 합니다.  

            1. **첫 번째 반박:**  
            - 찬성 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            2. **두 번째 반박:**  
            - 찬성 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            3. **세 번째 반박:**  
            - 찬성 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            이러한 이유로 찬성 측의 주장은 그리 강력하지 않습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][-3]}  
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"],prompt)
        elif step == 6:
            # 6. 찬성 측 변론
            result["speaker"] = "pos"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **찬성 측 입장에서 반대 측(negative)의 주장에 반박하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - **가장 최근의 반대 측 주장**을 검토하고 이에 대한 **논리적인 반박**을 제시하세요.  
            - 반대 측의 **핵심 논점을 직접적으로 반박**하세요.  
            - **근거, 논리적 추론, 현실 사례**를 활용하여 상대 주장을 논파하세요.  
            - 새로운 찬성 논거를 도입하지 말고, 오직 상대방의 주장을 반박하는 데 집중하세요.  

            ---

            ### **응답 형식:**  

            "반대 측의 주장을 면밀히 검토해 보았지만, 다음과 같은 이유로 반박하고자 합니다.  

            1. **첫 번째 반박:**  
            - 반대 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            2. **두 번째 반박:**  
            - 반대 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            3. **세 번째 반박:**  
            - 반대 측 주장 요약: "[상대방 주장 요약]"  
            - 논리적 반박: "[이 주장이 왜 논리적으로 문제가 있는지]"  
            - 근거 또는 예시: "[현실 사례 또는 논리적 근거]"  

            이러한 이유로 반대 측의 주장은 그리 강력하지 않습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][-3]}  
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 7:
            # 7. 판사가 최종 주장 시간 부여
            result["speaker"] = "judge_1"
            result["message"] = "이제 토론의 마지막 단계로 접어들고 있습니다. 양측 모두 최종 발언을 할 기회를 가지게 됩니다."

            time.sleep(1)

        elif step == 8:
            # 8. 찬성 측 최종 결론
            result["speaker"] = "pos"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **찬성 측 입장에서 최종 발언을 하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 찬성 측의 **가장 강력하고 설득력 있는 논거**를 요약하세요.  
            - **찬성 입장이 가장 논리적이고 정당한 이유**를 강조하세요.  
            - 반대 측의 반박을 언급하고, 왜 그것이 찬성 측의 입장을 약화시키지 않는지 설명하세요.  
            - **명확하고 설득력 있는 최종 결론**을 제시하세요.  

            ---

            ### **응답 형식:**  

            "이 토론을 통해 우리는 **{self.data['topic']}**이(가) 타당한 입장임을 명확히 입증하였습니다.  

            1. **핵심 논거 #1 요약:**  
            - "[가장 중요한 찬성 논거 요약]"  
            - "[반박에도 불구하고 여전히 유효한 이유]"  

            2. **핵심 논거 #2 요약:**  
            - "[또 다른 주요 찬성 논거 요약]"  
            - "[이 논거가 여전히 강력한 이유]"  

            3. **핵심 논거 #3 요약:**  
            - "[마지막 주요 논거 요약]"  
            - "[토론이 진행된 후에도 유지되는 이유]"  

            반대 측의 반박에도 불구하고, 우리의 주장은 **[결정적인 근거]** 때문에 흔들리지 않았습니다.  

            이번 토론을 통해 **{self.data['topic']}**이(가) 가장 논리적이고 정당한 입장이라는 것이 명확해졌습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][:-2]}  
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 9:
            # 9. 반대 측 최종 결론
            result["speaker"] = "neg"
            prompt = f"""
            당신은 **"{self.data['topic']}"** 주제에 대한 토론에 참여하고 있습니다. 당신의 역할은 **찬성 측 입장에서 최종 발언을 하는 것**입니다.  

            ### **진행 방식:**  
            - **반드시 한국어로만 말해야 합니다.**  
            - 찬성 측의 **가장 강력하고 설득력 있는 논거**를 요약하세요.  
            - **찬성 입장이 가장 논리적이고 정당한 이유**를 강조하세요.  
            - 반대 측의 반박을 언급하고, 왜 그것이 찬성 측의 입장을 약화시키지 않는지 설명하세요.  
            - **명확하고 설득력 있는 최종 결론**을 제시하세요.  

            ---

            ### **응답 형식:**  

            "이 토론을 통해 우리는 **{self.data['topic']}**이(가) 타당한 입장임을 명확히 입증하였습니다.  

            1. **핵심 논거 #1 요약:**  
            - "[가장 중요한 찬성 논거 요약]"  
            - "[반박에도 불구하고 여전히 유효한 이유]"  

            2. **핵심 논거 #2 요약:**  
            - "[또 다른 주요 찬성 논거 요약]"  
            - "[이 논거가 여전히 강력한 이유]"  

            3. **핵심 논거 #3 요약:**  
            - "[마지막 주요 논거 요약]"  
            - "[토론이 진행된 후에도 유지되는 이유]"  

            반대 측의 반박에도 불구하고, 우리의 주장은 **[결정적인 근거]** 때문에 흔들리지 않았습니다.  

            이번 토론을 통해 **{self.data['topic']}**이(가) 가장 논리적이고 정당한 입장이라는 것이 명확해졌습니다."  

            **토론 주제:** {self.data['topic']}  
            **이전 발언:** {self.data['debate_log'][:-2]}  
            """
            prompt += f"당신의 주장에서 독특한 특징을 강조하세요. {self.participant[result['speaker']].name}의 관점에서 생각해 보세요."
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 10:
            # 10. 판사가 판결 준비시간(1초) 부여
            result["speaker"] = "judge_1"
            result["message"] = "토론이 이제 종료되었습니다. 모든 주장을 검토한 후 최종 결정을 내리겠습니다."

            time.sleep(1)

        
        elif step == 11:
            # 11. 판사가 최종 결론
            result["speaker"] = "judge_1"
            result["message"] = self.evaluate()['result']
        
        # elif step == 12:
        #     result["speaker"] = "summerizer"
        #     # result["message"] = self.summerizer()['result']
        #     debate["status"]["type"] = "end"

        else:
            result["speaker"] = "SYSTEM"
            result["message"] = "토론이 이미 종료되었습니다."
        
        debate["debate_log"].append(result)
            # print(self.summerizer())
        # if result["speaker"] == "pos":
        #     debate["debate_log_pos"].append(result["message"])



        result["timestamp"] = datetime.now()

        if step < self.max_step:
            debate["status"]["step"] += 1

        return result





    def evaluate(self) -> dict:
        # 찬성, 반대측 각각 토론 로그
        pos_log = next((pos_message for pos_message in self.data["debate_log"] if pos_message["speaker"] == "pos"))
        neg_log = next((pos_message for pos_message in self.data["debate_log"] if pos_message["speaker"] == "neg"))
        # 찬성, 반대측 반박 로그 (step 5,6)
        pos_rebuttal = next((pos_message for pos_message in self.data["debate_log"] if pos_message["step"] == 6))
        neg_rebuttal = next((neg_message for neg_message in self.data["debate_log"] if neg_message["step"] == 5))

        
        # Generate the evaluation text from the judge
        prompt_logicality = f"""
        You are an expert in logical reasoning and argument analysis. Your task is to evaluate the logical soundness of the following two passages relative to each other on a 100-point scale.

        ### Your Expertise:
        - You are a highly skilled evaluator of logical consistency, reasoning structures, and argumentation strength.
        - Your assessment is based purely on logic, without bias or subjective opinions.
        - You follow a systematic approach to identify logical strengths and weaknesses.

        ### Evaluation Criteria:
        - Is the argument consistent and logically structured?
        - Does it avoid logical fallacies (e.g., black-and-white thinking, circular reasoning, red herrings)?
        - Does it provide well-supported claims with minimal weaknesses in reasoning?

        ### Task Instructions:
        1. Analyze each passage and highlight specific points where the argument is logically strong.
        2. Identify any logical fallacies or weaknesses, if present.
        3. Summarize your evaluation with a clear, concise explanation.
        4. Ensure that the final output includes a score at the end.

        **[Passage 1]**  
        {pos_log}

        **[Passage 2]**  
        {neg_log}

        ### Output Format:
        - **Passage 1 Analysis:** (Detailed analysis of logical strengths and weaknesses)
        - **Passage 1 Logical Soundness Score(pos): Score

        - **Passage 2 Analysis:** (Detailed analysis of logical strengths and weaknesses)
        - **Passage 2 Logical Soundness Score(neg): Score
        """



        prompt_rebuttal = f"""
        You are an expert in argument analysis and rebuttal effectiveness evaluation. Your task is to assess the **rebuttal strength** of the following two passages relative to each other on a 100-point scale.

        ### Your Expertise:
        - You specialize in evaluating the effectiveness of counterarguments and logical refutations.
        - Your assessment is **objective and based purely on logical rigor** without bias.
        - You systematically identify the strengths and weaknesses of each rebuttal.

        ### Evaluation Criteria:
        - Does the rebuttal directly address and dismantle the opposing argument effectively?
        - Does it use sound reasoning, logical consistency, and strong evidence?
        - Does it avoid logical fallacies such as strawman arguments, misrepresentation, or red herrings?
        - Is the rebuttal structured in a coherent and persuasive manner?

        ### Task Instructions:
        1. Analyze each passage’s **rebuttal strength**, identifying key points where the argument is particularly effective.
        2. Highlight any **logical weaknesses or fallacies** that undermine the rebuttal.
        3. Summarize the overall effectiveness of the rebuttal and how well it counters the opposing stance within the analysis.
        4. Provide a **final rebuttal strength score** on a **100-point scale**.

        **[Rebuttal 1]**  
        {pos_rebuttal}

        **[Rebuttal 2]**  
        {neg_rebuttal}

        ### Output Format:
        - **Rebuttal 1 Analysis:** (Detailed analysis of the logical strengths and weaknesses)
        - **Rebuttal 1 Strength Score (pos):** Score

        - **Rebuttal 2 Analysis:** (Detailed analysis of the logical strengths and weaknesses)
        - **Rebuttal 2 Strength Score (neg):** Score

        """ 


        prompt_persuasion = f"""
        You are an expert in argument analysis and persuasion assessment. Your task is to evaluate the **persuasiveness** of the following two passages relative to each other on a 100-point scale.

        ### Your Expertise:
        - You specialize in assessing the **persuasive strength** of arguments in debates and discussions.
        - Your evaluation considers both logical reasoning and rhetorical effectiveness.
        - Your judgment is **objective and based on structured analysis**, free from bias.

        ### Evaluation Criteria:
        - **Clarity & Coherence**: Is the argument presented in a clear, structured, and engaging manner?
        - **Logical Soundness**: Does the argument make sense logically and avoid fallacies?
        - **Use of Evidence**: Does the argument effectively use data, examples, or credible sources?
        - **Emotional & Rhetorical Appeal**: Does the argument skillfully use rhetorical strategies (e.g., ethos, pathos, logos) to convince the audience?
        - **Effectiveness in Anticipating & Addressing Counterarguments**: Does the argument proactively refute potential objections and strengthen its stance?

        ### Task Instructions:
        1. Analyze each passage’s **persuasive effectiveness**, identifying key elements that make the argument compelling.
        2. Highlight any **weaknesses or missed opportunities** in persuasion.
        3. Summarize how effectively the passage **convinces** its audience.
        4. Provide a **final persuasiveness score** on a **100-point scale**.

        **[Passage 1]**  
        {pos_log}

        **[Passage 2]**  
        {neg_log}

        ### Output Format:
        - **Passage 1 Analysis:** (Detailed analysis of persuasiveness, including strengths and weaknesses)
        - **Passage 1 Persuasiveness Score (pos): Score

        - **Passage 2 Analysis:** (Detailed analysis of persuasiveness, including strengths and weaknesses)
        - **Passage 2 Persuasiveness Score (neg): Score
        """

   

        def extract_score(pattern, text):
            """정규식을 사용하여 점수를 추출하고 정수로 변환하는 함수"""
            match = re.search(pattern, text)
            return int(match.group(1)) if match else 0  # 매칭이 안 되면 기본값 0 반환

        def calculate_score(judge, prompt):
            """텍스트 생성 후 점수를 추출하는 함수"""
            result_text = self.generate_text(judge, prompt)
            return extract_score(r'\(pos\)\:.*?(\d+)(?:\*|\/100)?', result_text), \
                extract_score(r'\(neg\)\:.*?(\d+)(?:\*|\/100)?', result_text)

        # 각 평가 기준에 대한 점수 추출
        logicality_pos, logicality_neg = calculate_score("judge_1", prompt_logicality)
        rebuttal_pos, rebuttal_neg = calculate_score("judge_2", prompt_rebuttal)
        persuasion_pos, persuasion_neg = calculate_score("judge_3", prompt_persuasion)

        # 최종 점수 계산
        weights = {"logicality": 0.4, "rebuttal": 0.35, "persuasion": 0.25}

        match_pos = (logicality_pos * weights["logicality"] + 
                    rebuttal_pos * weights["rebuttal"] + 
                    persuasion_pos * weights["persuasion"])

        match_neg = (logicality_neg * weights["logicality"] + 
                    rebuttal_neg * weights["rebuttal"] + 
                    persuasion_neg * weights["persuasion"])

        # 결과 출력
        print(f"match_pos: {match_pos}")
        print(f"match_neg: {match_neg}")

        if match_pos:
            if match_pos > match_neg:
                self.data["result"] = "positive"
            elif match_pos < match_neg:
                self.data["result"] = "negative"
            else:
                self.data["result"] = "draw"
        else:
            self.data["result"] = "draw"
        



        return {
            "result": self.data["result"],
            "logicality_pos": logicality_pos,
            "logicality_neg": logicality_neg,
            "rebuttal_pos": rebuttal_pos,
            "rebuttal_neg": rebuttal_neg,
            "persuasion_pos": persuasion_pos,
            "persuasion_neg": persuasion_neg,
            "match_pos": match_pos,
            "match_neg": match_neg
            }
    
    # def summerizer(self):
    #     prompt_summary=f"""
    #     다음은 토론에 대한 전체 기록입니다. 이를 아래 형식으로 한글로 요약해 주세요.

    #     "주제": [토론의 주요 주제를 간결하게 정리]  
    #     "찬성 측 주장": [찬성 측의 핵심 주장 요약]  
    #     "반대 측 주장": [반대 측의 핵심 주장 요약]  
    #     "찬성 측 변론": [찬성 측이 반론에 대응한 내용]  
    #     "반대 측 변론": [반대 측이 반론에 대응한 내용]  
    #     "최종 판결": [토론의 결론 또는 심사 결과 요약]  

    #     아래는 토론 기록입니다:
    #     {self.data['debate_log']}
    #     """
    #     return self.generate_text("summerizer", prompt_summary)

        