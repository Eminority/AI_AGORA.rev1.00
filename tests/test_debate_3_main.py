from test_debate_3 import Debate

def main():
    topic = "공격과 방어 중 공격이 더 유리한 전략이다."
    debate = Debate(topic)
    
    print("\n=== 토론 시작 ===\n")
    result = debate.start()
    
    print("\n=== 토론 결과 ===\n")
    print(result)

if __name__ == "__main__":
    main()
