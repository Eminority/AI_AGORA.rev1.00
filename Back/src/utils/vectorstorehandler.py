from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List

def create_embedding_model():
    """Updated HuggingFaceEmbeddings usage"""
    return HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")

def create_vectorstore(splits: List[Document], embedding_model):
    """분할된 문서(splits)를 FAISS 벡터스토어에 저장하고 반환한다."""
    vectordb = FAISS.from_documents(splits, embedding_model)
    return vectordb

class VectorStoreHandler:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        :param chunk_size: 텍스트 분할 시 청크 크기 (기본값: 500)
        :param chunk_overlap: 청크 간의 중복 길이 (기본값: 50)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = create_embedding_model()
        self.vectorstore = None
    
    def split_text(self, text: str) -> List[Document]:
        """
        주어진 텍스트를 일정한 크기의 청크로 분할하여 Document 객체 리스트로 반환한다.
        
        :param text: 원본 텍스트 (문자열)
        :return: 분할된 텍스트 청크 리스트 (List[Document])
        """
        if not isinstance(text, str):
            print(f"Error: Expected string, but got {type(text)}")
            return []
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        
        # 텍스트를 청크로 분할
        chunks = splitter.split_text(text)
        
        # 각 청크를 Document 객체로 변환
        documents = [Document(page_content=chunk) for chunk in chunks]
        return documents
    
    def vectorstoring(self, articles: List[dict]):
        """
        주어진 기사 리스트(articles)를 기반으로 벡터 스토어를 생성한다.
        
        각 기사는 dict 형태이며, "content", "title", "url" 등의 키를 포함한다.
        
        1. 유효한 기사만 필터링한다.
        2. 각 기사의 content를 split_text() 메서드로 Document 객체 리스트로 분할한다.
        3. 모든 Document를 하나의 리스트로 합친 후, FAISS.from_documents()를 사용하여 벡터 스토어를 생성한다.
        
        Returns:
            생성된 벡터스토어 객체.
        
        Raises:
            ValueError: 유효한 기사 내용이 없거나 벡터 스토어 생성에 실패한 경우.
        """
        # 1. 유효한 기사 필터링 (본문이 빈 문자열이거나 에러 문구인 경우 제외)
        valid_articles = [
            article for article in articles
            if article.get("content", "").strip() and 
               article.get("content", "").strip() != "❌ 본문을 가져오지 못했습니다."
        ]
        if not valid_articles:
            raise ValueError("유효한 기사 내용이 없습니다. 크롤링 데이터를 확인하세요.")
        
        # 2. 각 기사의 본문을 청크(Document 객체)로 분할
        all_documents = []
        for article in valid_articles:
            content = article["content"]
            docs = self.split_text(content)
            if docs:
                all_documents.extend(docs)
        
        if not all_documents:
            raise ValueError("문서를 분할한 결과, 유효한 텍스트 청크가 없습니다.")
        
        # 3. FAISS 벡터스토어 생성
        vectorstore = create_vectorstore(all_documents, self.embeddings)
        if not vectorstore:
            raise ValueError("벡터스토어 생성에 실패했습니다.")
        
        self.vectorstore = vectorstore
        return vectorstore
