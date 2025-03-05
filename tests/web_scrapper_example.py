import json
from web_scrapper import WebScrapper

def save_articles_to_file(topic, filename="scraped_articles.json"):
    """
    주어진 주제에 대해 스크래핑한 기사를 JSON 파일로 저장합니다.

    Args:
        topic (str): 검색 주제.
        filename (str): 저장할 파일 이름.
    """
    # WebScrapper 클래스의 인스턴스 생성 (최대 20개 기사)
    scrapper = WebScrapper(max_results=20)
    
    # 해당 주제로 기사를 검색 및 크롤링
    articles = scrapper.get_articles(topic)
    
    # 파일에 결과 저장 (JSON 형식)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print(f"총 {len(articles)}개의 기사가 '{filename}' 파일에 저장되었습니다.")

if __name__ == "__main__":
    # 사용자로부터 검색할 주제 입력 받기
    topic = "is coffee good for human?"
    save_articles_to_file(topic)
