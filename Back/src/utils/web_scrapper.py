import time
import random
import requests
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class WebScrapper:
    def __init__(self, api_keys: dict, max_results=5, headless=True):
        """
        초기화 메서드.
        
        Args:
            api_keys (dict): AI_Factory에서 전달된 API 키 딕셔너리
        """
        self.api_key = api_keys.get("GSE")  # AI_Factory에서 전달받은 값 사용
        self.max_results = max_results
        self.headless = headless
        if not self.api_key:
            raise KeyError("환경 변수에서 'GSE' 키를 찾을 수 없습니다. .env 파일을 확인하세요.")

        self.cx = os.getenv("CX")
        if not self.cx:
            raise ValueError("환경 변수에서 'CX' 값을 찾을 수 없습니다. .env 파일을 확인하세요.")

        self.driver = self._init_driver()

    def _init_driver(self):
        """
        Selenium WebDriver 초기화.

        Args:
            headless (bool): 브라우저 창을 표시할지 여부.

        Returns:
            webdriver.Chrome: 설정된 WebDriver 인스턴스.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")  # 창 없이 실행
        # options.add_argument("--disable-gpu") #gpu 사용
        options.add_argument("--no-sandbox")
        options.add_argument('--ignore-certificate-errors') #SSL 인증 무시
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def search_articles(self, query):
        """
        Google Custom Search API를 사용하여 뉴스 기사 링크를 검색.

        Args:
            query (str): 검색어.

        Returns:
            list: 뉴스 기사 원본 URL 리스트.
        """
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": f"{query} site:news.google.com",
            "cx": self.cx,
            "key": self.api_key,
            "num": self.max_results,
            "tbm": "nws"  # 뉴스 검색 모드
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Google 검색 API 오류 발생: {response.json()}")
            return []

        data = response.json()
        return [item["link"] for item in data.get("items", [])]

    def _extract_real_url(self):
        """
        Google 뉴스의 리디렉션 페이지에서 실제 기사 URL을 추출.

        Returns:
            str: 실제 기사 URL.
        """
        try:
            time.sleep(random.uniform(1, 2))  # 최소한의 대기시간 적용
            article_link_element = self.driver.find_element(By.TAG_NAME, "a")  # 첫 번째 링크 찾기
            real_url = article_link_element.get_attribute("href")  # 실제 기사 URL 가져오기
            return real_url
        except Exception as e:
            print(f"리디렉션 페이지에서 실제 기사 URL 추출 실패: {e}")
            return None

    def _fetch_article_content(self, url):
        """
        뉴스 기사 페이지에서 모든 텍스트 크롤링.

        Args:
            url (str): 뉴스 기사 URL.

        Returns:
            str: 기사 본문.
        """
        self.driver.get(url)
        time.sleep(random.uniform(1, 3))  # 페이지 로딩 대기 시간 최적화

        # Google 뉴스 리디렉션 페이지인지 확인
        if "google.com" in self.driver.current_url and "news" in self.driver.current_url:
            real_url = self._extract_real_url()
            if real_url:
                self.driver.get(real_url)  # 실제 기사 URL로 이동
                time.sleep(random.uniform(1, 2))  # 기사 페이지 로딩 대기 시간 최적화

        # 스크롤을 내려서 모든 콘텐츠가 로딩되도록 함
        self._scroll_down()

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # 페이지의 모든 텍스트 추출 (사이트마다 구조가 다르므로 최대한 많은 내용 크롤링)
        paragraphs = soup.find_all("p")
        article_text = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

        return article_text if article_text else "본문을 가져오지 못했습니다."

    def _scroll_down(self):
        """
        Selenium을 이용하여 페이지를 스크롤 다운하여 모든 콘텐츠를 로딩.
        """
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for _ in range(3):  # 스크롤 횟수 줄이기
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))  # 랜덤 대기
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height

    def get_articles(self, topic, num_articles=None):
        """
        주어진 주제에 대해 관련 기사를 검색하고 본문을 크롤링.

        Args:
            topic (str): 검색 주제.
            num_articles (int): 가져올 기사 수. (기본값은 설정된 max_results 값)

        Returns:
            list: 기사 본문 리스트.
        """
        num_articles = num_articles if num_articles else self.max_results
        article_links = self.search_articles(topic)

        articles_data = []
        for link in article_links[:num_articles]:  # 요청된 개수만큼 처리
            article_content = self._fetch_article_content(link)
            if article_content:
                articles_data.append({"content": article_content})

        return articles_data

    def quit_driver(self):
        """
        WebDriver 종료.
        """
        if self.driver:
            self.driver.quit()


# 실행 예시
if __name__ == "__main__":
    processor = DebateDataProcessor(max_results=3, headless=True)
    topic = "AI technology"
    
    articles = processor.get_articles(topic)

    # 결과 출력
    for idx, article in enumerate(articles, 1):
        print(f"기사 {idx}:\n{article['content']}...\n")  

    processor.quit_driver()
