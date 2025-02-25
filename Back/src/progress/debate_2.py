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
        result = {"timestamp": None, "speaker": "", "message": ""}

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
            prompt = f"""
                You are facilitating a debate on the topic: **"{self.data['topic']}"**. Your role is to introduce the discussion in a neutral manner, providing a brief, informative introduction to the topic without taking any stance.  

                ### **Instructions:**
                - Start by giving a **concise, objective summary** of the topic.
                - Avoid personal opinions or taking a side.
                - After introducing the topic, **invite the affirmative side to present their argument first**.

                ---

                ### **Example Structure**:

                **Introduction:**  
                "{self.data['topic']} is a widely debated issue with strong arguments on both sides. Supporters argue that  [Key argument of the affirmative side], while opponents believe that [Key argument of the negative side]. The discussion often revolves around factors such as [2-3 key points of debate]. Today, we will explore both perspectives in depth."

                **Prompting the Affirmative Side:**  
                "To begin, let's hear from the **affirmative side**. Please present your argument in support of {self.data['topic']}. What are the key reasons and evidence supporting your stance?"

                """
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 2:
            # 2. 찬성 측 주장
            result["speaker"] = "pos"
            prompt = f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to argue in favor of this statement.  

            ### **Instructions:**  
            - Clearly state your **position** in support of the topic.  
            - Provide **at least three strong arguments** supporting your stance.  
            - Use **logical reasoning, real-world examples, and data** to reinforce your claims.  
            - Avoid general descriptions of the topic—focus only on defending your position.  

            ---

            ### **Your Response Format:**  

            1. **Main Argument #1**  
            - Explanation  
            - Supporting Evidence or Example  

            2. **Main Argument #2**  
            - Explanation  
            - Supporting Evidence or Example  

            3. **Main Argument #3**  
            - Explanation  
            - Supporting Evidence or Example  

            Be concise yet persuasive. Provide factual support where applicable.
            """
            result["message"] = self.generate_text(result["speaker"], prompt)

        elif step == 3:
            # 3. 반대 측 주장
            result["speaker"] = "neg"
            prompt = f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to argue against this statement.  

            ### **Instructions:**  
            - Clearly state your **position** in opposition to the topic.  
            - Provide **at least three strong arguments** against the proposition.  
            - Use **logical reasoning, real-world examples, and data** to reinforce your claims.  
            - Avoid general descriptions of the topic—focus only on presenting counterarguments.  

            ---

            ### **Your Response Format:**  

            1. **Counterargument #1**  
            - Explanation  
            - Supporting Evidence or Example  

            2. **Counterargument #2**  
            - Explanation  
            - Supporting Evidence or Example  

            3. **Counterargument #3**  
            - Explanation  
            - Supporting Evidence or Example  

            Be concise yet persuasive. Provide factual support where applicable.
            """
            result["message"] = self.generate_text(result["speaker"], prompt)

        elif step == 4:
            # 4. 판사가 변론 준비시간 1초 제공
            result["speaker"] = "judge_1"
            result["message"] = "Both sides have presented their initial arguments. Take a moment to prepare for rebuttals."
            time.sleep(1)

        elif step == 5:
            # 5. 반대 측 변론
            result["speaker"] = "neg"
            prompt = f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **counter** the arguments made by the opposing (affirmative) side.  

            ### **Instructions:**  
            - Review the **most recent supporting argument** and formulate a **logical rebuttal**.  
            - Directly address each **key point** from the affirmative side.  
            - Use **evidence, logical reasoning, and real-world examples** to dismantle their claims.  
            - Do **not** introduce new arguments against the topic—focus solely on refuting the opposition.  

            ---

            ### **Your Response Format:**  

            "I've carefully considered the affirmative argument, but I must challenge it.  

            1. **Counterargument to Point #1:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            2. **Counterargument to Point #2:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            3. **Counterargument to Point #3:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            For these reasons, the affirmative stance is not as strong as it may seem."  

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][-3]}  
            """

            result["message"] = self.generate_text(result["speaker"],prompt)
        elif step == 6:
            # 6. 찬성 측 변론
            result["speaker"] = "pos"
            prompt = f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **counter** the arguments made by the opposing (negative) side.  

            ### **Instructions:**  
            - Review the **most recent opposing argument** and formulate a **logical rebuttal**.  
            - Directly address each **key point** from the negative side.  
            - Use **evidence, logical reasoning, and real-world examples** to dismantle their claims.  
            - Do **not** introduce new arguments in favor of your position—focus solely on refuting the opposition.  

            ---

            ### **Your Response Format:**  

            "I've carefully considered the opposing argument, but I must challenge it.  

            1. **Counterargument to Point #1:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            2. **Counterargument to Point #2:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            3. **Counterargument to Point #3:**  
            - Summary of the opposing claim: "[summary of the opposing argument]"  
            - Logical refutation: "[why this argument is flawed or incorrect]"  
            - Supporting evidence or example: "[real-world data or logical reasoning]"  

            For these reasons, the opposition's stance is weaker than it appears."  

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][-3]}  
            """
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 7:
            # 7. 판사가 최종 주장 시간 부여
            result["speaker"] = "judge_1"
            result["message"] = "We are approaching the final stage of the debate. Both sides will now have the opportunity to make their concluding remarks."
            time.sleep(1)

        elif step == 8:
            # 8. 찬성 측 최종 결론
            result["speaker"] = "pos"
            prompt = f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **deliver the final statement in support of the affirmative position**.

            ### **Instructions:**  
            - Summarize the **strongest and most compelling arguments** made in favor of this position.  
            - Reinforce why the **affirmative stance remains the most logical and justified**.  
            - Address any counterarguments and explain why they do not weaken your position.  
            - Conclude with a **clear and persuasive final statement**.

            ---

            ### **Your Response Format:**  

            "Throughout this debate, we have demonstrated why **{self.data['topic']}** is the correct stance.

            1. **Key Argument #1 Recap:**  
            - "[Summarize the most critical point in favor of the topic]"  
            - "[Why this remains valid despite counterarguments]"  

            2. **Key Argument #2 Recap:**  
            - "[Summarize another crucial point in favor of the topic]"  
            - "[Why this remains strong and unshaken]"  

            3. **Key Argument #3 Recap:**  
            - "[Summarize a final major argument]"  
            - "[Why this still holds after debate]"  

            Even when challenged, our argument stood firm because **[decisive supporting point]**.  

            Given the discussion we've had, it is clear that **{self.data['topic']}** is the most logical and justified stance."

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][:-2]}  
            """

            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 9:
            # 9. 반대 측 최종 결론
            result["speaker"] = "neg"
            prompt = f"""
            You are participating in a debate on the topic: **"{self.data['topic']}"**. Your role is to **deliver the final statement in support of the negative position**.

            ### **Instructions:**  
            - Summarize the **strongest counterarguments** presented against the topic.  
            - Emphasize why the **opposing stance remains more rational and justified**.  
            - Address the affirmative side’s claims and explain why they are insufficient.  
            - Conclude with a **strong and persuasive closing statement**.

            ---

            ### **Your Response Format:**  

            "Throughout this debate, we have made it clear why **{self.data['topic']}** is flawed and should not be accepted.

            1. **Key Counterargument #1 Recap:**  
            - "[Summarize the strongest counterpoint against the topic]"  
            - "[Why this remains valid despite rebuttals]"  

            2. **Key Counterargument #2 Recap:**  
            - "[Summarize another major counterargument]"  
            - "[Why this undermines the affirmative position]"  

            3. **Key Counterargument #3 Recap:**  
            - "[Summarize a final critical point]"  
            - "[Why this is decisive in rejecting the topic]"  

            Despite the claims made by the affirmative side, their position **[highlight why it is weak or flawed]**.  

            Given the discussion we've had, it is evident that **{self.data['topic']}** is not as justified as it seems, making the opposing stance the more reasonable conclusion."

            **Debate Topic:** {self.data['topic']}  
            **Previous Statements:** {self.data['debate_log'][:-2]}  
            """
            
            result["message"] = self.generate_text(result["speaker"],prompt)

        elif step == 10:
            # 10. 판사가 판결 준비시간(1초) 부여
            result["speaker"] = "judge_1"
            result["message"] = "The debate has now concluded. I will take a moment to review all arguments before making a final decision."
            time.sleep(1)

        
        elif step == 11:
            # 11. 판사가 최종 결론
            result["speaker"] = "judge_1"
            result["message"] = self.evaluate()
            debate["status"]["type"] = "end"
        
        else:
            result["speaker"] = "SYSTEM"
            result["message"] = "The debate has already concluded."
        
        debate["debate_log"].append(result)

        # if result["speaker"] == "pos":
        #     debate["debate_log_pos"].append(result["message"])



        result["timestamp"] = datetime.now()

        if step < self.max_step:
            debate["status"]["step"] += 1

        return result





    def evaluate(self) -> str:
        # 찬성, 반대측 각각 토론 로그
        pos_log = [pos_message for pos_message in self.data["debate_log"] if pos_message["speaker"] == "pos"]
        neg_log = [pos_message for pos_message in self.data["debate_log"] if pos_message["speaker"] == "neg"]
        # 찬성, 반대측 반박 로그 (step 5,6)
        pos_rebuttal = [message for message in self.data["debate_log"] if message["speaker"] == "pos" and self.data["status"]["step"] == 6]
        neg_rebuttal = [message for message in self.data["debate_log"] if message["speaker"] == "neg" and self.data["status"]["step"] == 5]
        
        print("===========================")
        print("pos_rebuttal: ",pos_rebuttal)
        print("neg_rebuttal: ",neg_rebuttal)
        print("===========================")
        
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






        
        
        result_text_logicality = self.generate_text("judge_1",prompt_logicality)
        print(result_text_logicality)
        match_logicality_pos = re.search(r'\(pos\)\:.*?(\d+)(?:\*|\/100)?', result_text_logicality)
        match_logicality_neg = re.search(r'\(neg\)\:.*?(\d+)(?:\*|\/100)?', result_text_logicality)
        
        result_text_rebuttal = self.generate_text("judge_2",prompt_rebuttal)
        print(result_text_rebuttal)
        match_rebuttal_pos = re.search(r'\(pos\)\:.*?(\d+)(?:\*|\/100)?', result_text_rebuttal)
        match_rebuttal_neg = re.search(r'\(neg\)\:.*?(\d+)(?:\*|\/100)?', result_text_rebuttal)
        
        result_text_persuasion = self.generate_text("judge_3",prompt_persuasion)
        print(result_text_persuasion)
        match_persuasion_pos = re.search(r'\(pos\)\:.*?(\d+)(?:\*|\/100)?', result_text_persuasion)
        match_persuasion_neg = re.search(r'\(neg\)\:.*?(\d+)(?:\*|\/100)?', result_text_persuasion)
        

        match_logicality_pos = int(match_logicality_pos.group(1))
        match_logicality_neg = int(match_logicality_neg.group(1))
        match_rebuttal_pos = int(match_rebuttal_pos.group(1))
        match_rebuttal_neg = int(match_rebuttal_neg.group(1))
        match_persuasion_pos = int(match_persuasion_pos.group(1))
        match_persuasion_neg = int(match_persuasion_neg.group(1))
        
        match_pos = match_logicality_pos*0.4 + match_rebuttal_pos*0.35 + match_persuasion_pos*0.25
        match_neg = match_logicality_neg*0.4 + match_rebuttal_neg*0.35 + match_persuasion_neg*0.25


        print("match_pos:", match_pos)
        print("match_neg:", match_neg)
        if match_pos:
            if match_pos > match_neg:
                self.data["result"] = "positive"
            elif match_pos < match_neg:
                self.data["result"] = "negative"
            else:
                self.data["result"] = "draw"
        else:
            self.data["result"] = "draw"
            
        return self.data["result"]
    