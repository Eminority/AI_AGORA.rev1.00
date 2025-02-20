from abc import ABC, abstractmethod

class Progress(ABC):
    """
    ai끼리의 대화를 진행시키기 위한 모듈의 상위 클래스
    progress, evaluate method 구현 필요.
    self.participant에 참가할 ai 객체를 dict 형태로 가지고 있을 것.
    self.data에 저장할 데이터 dict를 가지고 있을 것.
    """
    def __init__(self):
        self.participant = {}
        self.data = {}
        self.vectorstore = None

    @abstractmethod
    def progress(self):
        pass

    @abstractmethod
    def evaluate(self):
        pass