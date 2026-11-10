import os
from functools import lru_cache
from pathlib import Path

from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from pypdf import PdfReader
from langchain_classic.retrievers import BM25Retriever
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from nltk.tokenize import word_tokenize
from langchain_core.documents import Document

from config.error_handler import retry_with_backoff
from config.logging_handler import get_logger
from config.model_config import ModelTier, model_endpoint


# LOG INSTANTIATION
log = get_logger("rag_agent")
# VECTOR STORE FILE ABSOLUTE PATH
VECTORDB_DIR = Path(__file__).resolve().parent.parent / "config"


# DOCUMENT INDEXING & RETRIEVAL
def Indexing():
    """Initialize document loader, splitter, embeddings, and vector store."""
    # updated : document loader 
    def load_pdf_pages(file_path: str) -> list[Document]:
        reader = PdfReader(file_path)
        return [
            Document(
                page_content=page.extract_text() or "",
                metadata={"source": file_path, "page": i},
            )
            for i, page in enumerate(reader.pages)
        ]
    
    file_path =(
        "D:/Documents/Project_x/x v5/eit-digital-artificial-intelligence-report.pdf"
    )
    documents = load_pdf_pages(file_path)
    

    # Text splitter
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4",
        chunk_size=500,
        chunk_overlap=50,
    )
    splitted_documents = splitter.split_documents(documents)

    # Embeddings
    embeddings = HuggingFaceEmbeddings(model="intfloat/e5-small-v2")

    # Vector store
    vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory=str(VECTORDB_DIR),
    )

    if not os.path.exists(VECTORDB_DIR / "chroma.sqlite3"):
        vector_store.add_documents(documents=splitted_documents)

    return build_retrievers(vector_store, splitted_documents)


def build_retrievers(vector_store, splitted_documents):
    """Build BM25 and Chroma retrievers and merge them using ensemble."""
    # BM25 retriever
    bm25_retriever = BM25Retriever.from_documents(
        splitted_documents,
        k=8,
        preprocess_func=word_tokenize,
    )

    # Chroma retriever
    chroma_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 8},
    )

    # Ensemble retriever
    return EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.5, 0.5],
        c=60,
    )


@lru_cache(maxsize=1)
def get_retriever():
    return Indexing()


# TOOLS DECORATOR
@tool
async def search_docs(query: str) -> str:
    """
    A search tool that search the given corpus for user's query.
    Always provide the answer from the provided documents
    Use this when you need factual information from the material you've been provided.
    """
    try:
        result = await get_retriever().ainvoke(query)
        # chunks = []
        # for doc in result:
        #     chunks.append(doc.page_content)

        # comprehension combined with XML tagging
        formatted_chunks = [
            f"<document index='{index}'>\n{document.page_content}\n</document>"
            for index, document in enumerate(result)
        ]
        return "\n".join(formatted_chunks)
    except Exception as e:
        log.exception("search_docs retriever failed: %s", str(e))
        raise


# AGENT CONFIGURATION
def create_rag_tool():
    model = model_endpoint(ModelTier.fast)
    if model is None:
        raise RuntimeError("No model endpoint configured for the RAG agent.")

    rag_agent = create_agent(
        model=model,
        tools=[search_docs],
        system_prompt="""
        Role:You're an agent with external knowledge base with context.
             You always use your tool to retrieve data from external database when user ask context speciic question

        Constraints: Use the following pieces of retrieved context to answer the question.
                     If you don't know the answer, just say that you don't know.
                     Do not produce wrong answer with confidence.

        Output_format: Accurate, Precise and Meaningful.
                       'strictly' Paraphrase, never quote directly
        """,
    )

    @retry_with_backoff()
    async def invoke_rag(query: str) -> str:
        try:
            result = await rag_agent.ainvoke(
                {"messages": [HumanMessage(content=query)]}
            )
        except Exception:
            log.exception("rag agent invoke failed")
            raise

        content = result["messages"][-1].content
        if isinstance(content, list):
            return " ".join(
                block["text"]
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        return content

    # Response handler
    @tool
    async def rag(query: str) -> str:
        """
        High performing sub agent retrieval augmented generator.
        Provide clean response for main agent.
        Provide precise answer with no gibberish.
        Never ask questions.

        Args:
            query: The user query string

        Returns:
            The final response of agent.
        """
        return await invoke_rag(query)

    return rag
