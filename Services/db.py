from logging import getLogger
import os
from typing import List, Union
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os
logger = getLogger(__name__)
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
        logger.info("Initializing TextRAGVectorStore", extra={"paths": paths})
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
    def _load_pdf_documents(self, path: str) -> List:
        logger.info("Loading PDF document", extra={"path": path})
        loader = PyPDFLoader(path)
        documents = loader.load()
        logger.info(
            "PDF loaded successfully",
            extra={"path": path, "pages": len(documents)}
        )
        return documents

    
    # def _load_documents(self, paths) -> List:
    #     """Load documents from given paths.
    #     Args:   paths (str | List[str]): Path or list of paths to text files
    #     returns:
    #         List: List of loaded documents"""
    #     logger.info("Loading documents", extra={"paths": paths})
    #     documents = []

    #     if isinstance(paths, str):
    #         loader = TextLoader(paths, encoding="utf-8")
    #         documents.extend(loader.load())

    #     elif isinstance(paths, list):
    #         for path in paths:
    #             loader = TextLoader(path, encoding="utf-8")
    #             documents.extend(loader.load())

    #     return documents
    
    

    def _load_documents(self, paths) -> List:
        """Load documents from given paths.
        Args:   paths (str | List[str]): Path or list of paths to text files
        returns:
            List: List of loaded documents"""
            
        logger.info(f"Loading documents{paths} ", extra={"paths": paths})
        documents = []

        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            ext = os.path.splitext(path)[1].lower()

            if ext == ".txt":
                loader = TextLoader(path, encoding="utf-8")
                documents.extend(loader.load())

            elif ext == ".pdf":
                documents.extend(self._load_pdf_documents(path))

            else:
                logger.warning(
                    "Unsupported file type skipped",
                    extra={"path": path}
                )

        return documents

    # -------------------------------
    # Split documents
    # -------------------------------
    def _split_documents(self, documents):
        """Takes in a list of documents and splits them into chunks. 
        args:
            documents (List): List of documents to be split
            returns:
                List: List of split documents"""
                
        logger.info("Splitting documents", extra={"num_documents": len(documents)})
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
        )
        return splitter.split_documents(documents)
    
    # -------------------------------
    # Public: Add new data
    # -------------------------------
    # def add_data(self, paths: Union[str, List[str]]):
    #     """Add data to the vector store.
    #     Args:
    #         paths (str | List[str]): Path or list of paths to text files
    #     Returns:
    #         None"""
    #     logger.info("Adding data to vector store", extra={"paths": paths})
    #     documents = self._load_documents(paths)
    #     chunks = self._split_documents_Txt(documents)

    #     self.vectorstore.add_documents(chunks)
    #     print(f"Added {len(chunks)} chunks to vector DB")
        
    def add_data(self, paths: Union[str, List[str]]):
        """Add data to the vector store.
        Args:
            paths (str | List[str]): Path or list of paths to text files
        Returns:
            None"""
        
        logger.info("Adding data to vector store", extra={"paths": paths})

        documents = self._load_documents(paths)
        chunks = self._split_documents(documents)

        self.vectorstore.add_documents(chunks)
        logger.info(
            "Data ingestion completed",
            extra={"chunks_added": len(chunks)}
        )


    # -------------------------------
    # Query
    # -------------------------------
    def query(self, question: str):
        """Query the vector store.
         args:
            question (str): The question to query
            returns:
                List: List of retrieved documents"""
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
      