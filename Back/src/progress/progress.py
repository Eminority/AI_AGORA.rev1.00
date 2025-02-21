from abc import ABC, abstractmethod

class Progress(ABC):
    """
    ai끼리의 대화를 진행시키기 위한 모듈의 상위 클래스
    progress, evaluate method 구현 필요.
    self.participant에 참가할 ai 객체를 dict 형태로 가지고 있을 것.
    self.data에 저장할 데이터 dict를 가지고 있을 것.
    사용되는 generate_text에 들어갈 설정값을 config에 쥐고있을 것.
    """
    def __init__(self, participant:dict, data:dict, generate_text_config:dict):
        """
        participant:{"position":Participant_instance}
        data: progress_data(저장할 데이터 전체)
        generate_text_config: progress 내부에서 응답하는데 사용할 설정값들
        """
        self.participant = participant
        self.data = data
        self.generate_text_config = generate_text_config
        self.vectorstore = None

    @abstractmethod
    def progress(self):
        pass

    @abstractmethod
    def evaluate(self):
        pass

    def generate_text(self, speaker:str, prompt:str) -> str:
        speaker_ai = self.participant.get(speaker, {})
        if speaker_ai:
            speaker_ai = speaker_ai.ai_instance
        if (speaker_ai):
            return speaker_ai.generate_text(user_prompt = prompt,
                                            max_tokens = self.generate_text_config["max_tokens"],
                                            temperature = self.generate_text_config["temperature"]
                                            )
        else:
            return "speaker의 ai가 설정되어있지 않습니다."

    def generate_text_with_vectorstore(self, speaker:str, prompt:str) ->str:
        speaker_ai = self.participant.get(speaker, {})
        if speaker_ai:
            speaker_ai = speaker_ai.ai_instance
        if (speaker_ai):
            return speaker_ai.generate_text_with_vectorstore(user_prompt = prompt,
                                            max_tokens = self.generate_text_config["max_tokens"],
                                            temperature = self.generate_text_config["temperature"],
                                            vectorstore = self.vectorstore,
                                            k = self.generate_text_config["k"]
                                            )
        else:
            return "speaker의 ai가 설정되어있지 않습니다."