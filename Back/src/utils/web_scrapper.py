import requests
import concurrent.futures
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

class WebScrapper:
    def __init__(self, max_results=20):
        """
        초기화 메서드.
        
        Args:
            max_results (int): 가져올 뉴스 기사 수
        """
        self.max_results = max_results  
        self.max_search = 1000  # 검색 최대 개수 

        # 크롤링 불가능한 사이트 리스트
        self.blocked_sites = set([
            "msn.com", "www.fnnews.com", "www.hani.co.kr", "www.moneycontrol.com", "www.mcknights.com",
            "abcnews.go.com", "www.thedailybeast.com", "www.msnbc.com", "www.business-standard.com",
            "www.reuters.com", "www.washingtonpost.com", "www.nationalreview.com", "www.newsweek.com"
        ])

    def search_articles(self, query):
        """
        DuckDuckGo에서 뉴스 검색 후 크롤링 불가능한 사이트를 제외한 URL 리스트 반환

        Args:
            query (str): 검색어

        Returns:
            list: 뉴스 기사 URL 리스트
        """
        news_data = []
        
        with DDGS() as ddgs:
            for result in ddgs.news(query, max_results=self.max_search):  # 최대 1000개 검색
                domain = result["url"].split("/")[2]  # URL에서 도메인 추출

                # 크롤링 불가능한 사이트 필터링
                if any(site in domain for site in self.blocked_sites):
                    continue  

                news_data.append(result["url"])

                # 유효한 기사 개수가 max_results에 도달하면 중단
                if len(news_data) >= self.max_results:
                    break

        return news_data

    def _fetch_article_content(self, url):
        """
        뉴스 기사 URL에서 본문을 크롤링하는 함수

        Args:
            url (str): 뉴스 기사 URL

        Returns:
            str: 기사 본문
        """
        try:
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return f"❌ 요청 실패 (Status Code: {response.status_code})"

            soup = BeautifulSoup(response.text, "html.parser")

            # 일반적인 뉴스 사이트의 본문 선택지
            possible_selectors = [
                "article", "div.article-body", "div.story-body",
                "div.post-content", "div.entry-content", "div.main-content",
                "section.article", "div#main-content", "div.text", "div.content",
                "div[class*='article']", "div[class*='content']", "div[class*='body']", 
                "p"
            ]

            article_text = ""
            for selector in possible_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    paragraphs = elem.find_all("p")
                    if paragraphs:
                        article_text += "\n".join([p.get_text() for p in paragraphs]) + "\n\n"

            if not article_text.strip():
                # 크롤링 실패한 사이트를 차단 목록에 추가
                domain = url.split("/")[2]
                if domain not in self.blocked_sites:
                    self.blocked_sites.add(domain)
                    
                return "❌ 본문을 찾을 수 없습니다. (HTML 구조 확인 필요)"

            return article_text.strip()

        except Exception as e:
            return f"❌ 크롤링 중 오류 발생: {str(e)}"

    def get_articles(self, topic):
        """
        주어진 주제에 대해 관련 기사를 검색하고 본문을 크롤링

        Args:
            topic (str): 검색 주제

        Returns:
            list: {"content" : 기사 본문 리스트}
        """
        article_links = self.search_articles(topic)

        articles_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self._fetch_article_content, link): link for link in article_links}

            for future in concurrent.futures.as_completed(future_to_url):
                article_content = future.result()
                if article_content:
                    articles_data.append({"content": article_content})

        return articles_data

