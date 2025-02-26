from test_debate_3 import Debate

def main():
    topic = "코카콜라가 펩시콜라보다 더 뛰어나다."
    debate = Debate(topic)
    
    print("\n=== 토론 시작 ===\n")
    result = debate.progress()
    
    print("\n=== 토론 결과 ===\n")
    print(result)

if __name__ == "__main__":
    main()
