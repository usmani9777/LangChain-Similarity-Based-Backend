from typing import List, Union
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextRAGVectorStore:
    def __init__(
        self,
        paths: Union[str, List[str]],
        persist_directory: str = "./chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 3,
        rebuild: bool = False,   # 👈 control re-indexing
    ):
        """Initialize the TextRAGVectorStore.
        Args: 
            paths (str): defines the path where we save the file
            
        Returns:
            Name (Str): Name of the file saved
        """
        self.paths = paths
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model
        )

        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.top_k}
        )

        if rebuild:
            self.add_data(self.paths)

    # -------------------------------
    # Load documents (single / list / folder)
    # -------------------------------
    def _load_documents(self, paths) -> List:
        documents = []

        if isinstance(paths, str):
            loader = TextLoader(paths, encoding="utf-8")
            documents.extend(loader.load())

        elif isinstance(paths, list):
            for path in paths:
                loader = TextLoader(path, encoding="utf-8")
                documents.extend(loader.load())

        return documents

    # -------------------------------
    # Split documents
    # -------------------------------
    def _split_documents(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return splitter.split_documents(documents)

    # -------------------------------
    # Public: Add new data
    # -------------------------------
    def add_data(self, paths: Union[str, List[str]]):
        documents = self._load_documents(paths)
        chunks = self._split_documents(documents)

        self.vectorstore.add_documents(chunks)
        print(f"Added {len(chunks)} chunks to vector DB")

    # -------------------------------
    # Query
    # -------------------------------
    def query(self, question: str):
        return self.retriever.invoke(question)
    
# if __name__ == "__main__":
#     rag = TextRAGVectorStore(
#         paths=["file.txt"],
#         rebuild=True
#     )
    
      
#     rag.add_data("file1.txt")
#     rag.add_data("file2.txt")
    
#     results = rag.query("What is Code of conduct?")
#     for i, r in enumerate(results, 1):
#         print(f"\nResult {i}:\n{r.page_content}")
      