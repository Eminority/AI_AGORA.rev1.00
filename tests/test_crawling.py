import requests
import concurrent.futures
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from time import time

# ✅ 크롤링이 불가능한 사이트 리스트 (여기에 추가 가능)
blocked_sites = set(["msn.com", "www.fnnews.com", "www.hani.co.kr", "www.moneycontrol.com", "www.mcknights.com", 
                     "abcnews.go.com", "www.thedailybeast.com", "www.msnbc.com", "www.business-standard.com",
                     "www.reuters.com", "www.washingtonpost.com", "www.nationalreview.com", "www.newsweek.com"])

time_1 = time()
def search_news_articles(query, max_search=1000, max_results=20):
    """
    덕덕고에서 뉴스 검색 후 크롤링 불가능한 사이트를 제외한 URL 리스트 반환
    """
    with DDGS() as ddgs:
        results = list(ddgs.news(query, max_results=max_search))

    news_data = []
    for result in results:
        domain = result["url"].split("/")[2]  # URL에서 도메인 추출

        # ✅ 크롤링 불가능한 사이트 자동 필터링
        if any(site in domain for site in blocked_sites):
            print(f"🚫 필터링된 사이트: {domain} (크롤링 차단됨)")
            continue  

        news_data.append({
            "title": result["title"],
            "url": result["url"],
            "domain": domain
        })

        # ✅ 최대 크롤링할 기사 개수 도달 시 중단
        if len(news_data) >= max_results:
            break

    return news_data

def crawl_news_article(url):
    """
    뉴스 기사 URL에서 본문을 크롤링하는 함수 (병렬 실행 가능)
    """
    try:
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return {"url": url, "content": f"❌ 요청 실패 (Status Code: {response.status_code})"}

        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ 일반적인 뉴스 사이트의 본문 선택지
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
            # ✅ 크롤링 실패한 사이트를 차단 목록에 추가
            domain = url.split("/")[2]
            if domain not in blocked_sites:
                blocked_sites.add(domain)
                print(f"⚠️ 크롤링 불가 사이트 추가됨: {domain}")

            return {"url": url, "content": "❌ 본문을 찾을 수 없습니다. (HTML 구조 확인 필요)"}

        return {"url": url, "content": article_text.strip()}

    except Exception as e:
        return {"url": url, "content": f"❌ 크롤링 중 오류 발생: {str(e)}"}

def parallel_crawl(news_list, max_workers=10):
    """
    병렬로 여러 개의 뉴스 기사 본문을 크롤링하는 함수
    """
    final_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # ✅ 병렬 처리 실행 (각 URL 크롤링)
        future_to_url = {executor.submit(crawl_news_article, news["url"]): news for news in news_list}

        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            final_results.append(result)

            # ✅ 크롤링 결과 출력
            print(f"\n📄 기사 본문 (URL: {result['url']}):")
            print(result["content"][:500])  # 너무 길면 앞부분만 출력
            print("=" * 80)

    return final_results

# ✅ 뉴스 검색 및 병렬 크롤링 실행
search_query = "Is it beneficial to walk your pet?"
max_articles = 20  # 최종 크롤링할 기사 개수

print(f"\n=== 🔍 '{search_query}' 검색 중 (최대 {max_articles}개 기사) ===\n")
news_results = search_news_articles(search_query, max_search=1000, max_results=max_articles)

# ✅ 병렬 크롤링 실행
print("\n🚀 병렬 크롤링 시작...")
final_articles = parallel_crawl(news_results, max_workers=10)

print(f"\n✅ {max_articles}개 뉴스 크롤링 완료!")
time_2 = time()
print(f"걸린 시간 : {time_2-time_1:.2f}")