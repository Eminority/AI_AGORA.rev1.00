import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_articles_to_text_file(
    input_filename="scraped_articles.json",
    output_filename="split_articles_5.txt",
    chunk_size=1024,
    chunk_overlap=64
):
    """
    1) input_filename에 저장된 기사 본문을 불러온다.
    2) RecursiveCharacterTextSplitter로 기사 본문을 분할한다.
    3) 결과를 output_filename(텍스트 파일)에 콘솔 출력 형식으로 저장한다.
    """
    # JSON 파일 로드
    with open(input_filename, "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    # Splitter 설정
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    # 텍스트 파일로 결과 저장
    with open(output_filename, "w", encoding="utf-8") as out_file:
        for idx, article in enumerate(articles, start=1):
            content = article.get("content", "")
            if not content.strip():
                continue

            # 기사 본문을 청크로 분할
            chunks = splitter.split_text(content)
            
            # 기사별 헤더 작성
            out_file.write(f"[Article {idx}] 총 {len(chunks)}개의 청크 생성됨:\n\n")
            
            # 분할된 청크들을 순서대로 작성
            for i, chunk in enumerate(chunks, start=1):
                out_file.write(f"--- 청크 {i} ---\n")
                out_file.write(chunk.strip() + "\n\n")
            
            out_file.write("=" * 50 + "\n\n")  # 기사 간 구분선

    print(f"총 {idx}개의 기사가 분할되어 '{output_filename}'에 저장되었습니다.")

if __name__ == "__main__":
    split_articles_to_text_file()
