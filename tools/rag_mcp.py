# Standard library imports
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import cast

# Third-party imports
from dotenv import load_dotenv
from nltk.tokenize import word_tokenize

# LangChain imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.language_models.chat_models import BaseChatModel

# Local imports
from config.error_handler import retry_with_backoff
from mcp.server.fastmcp import FastMCP
from config.model_config import model_endpoint, ModelTier
from config.logging_handler import get_logger

# CONFIGURATION & INITIALIZATION
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
load_dotenv(override=True)

# TOOL NAME
mcp = FastMCP("rag_subagent")

# LOG INSTANTIATION
log = get_logger("mcp/rag")

# LLM CONFIGURATION
llm = cast(BaseChatModel, model_endpoint(ModelTier.fast))

# VECTOR STORE FILE ABSOLUTE PATH
CURRENT_DIR = Path(__file__).resolve().parent.parent
VECTORDB_DIR = CURRENT_DIR / "config" 

# DOCUMENT INDEXING & RETRIEVAL
def Indexing():
    """Initialize document loader, splitter, embeddings, and vector store."""
    
    # Document loader
    loader = PyPDFLoader(
        file_path=Path(r"D:\Documents/Project_x/x v5/eit-digital-artificial-intelligence-report.pdf"),
        mode="single",
        extract_images=False,
        extraction_mode="layout",
    )
    documents = loader.load()

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
        persist_directory= str(VECTORDB_DIR)
    )

    if os.path.exists(Path(str(VECTORDB_DIR / "chroma.sqlite3"))):
        ensemble = build_retrievers(vector_store, splitted_documents)
        return ensemble
    else:
        vector_store.add_documents(documents=splitted_documents)
        ensemble = build_retrievers(vector_store, splitted_documents)
        return ensemble


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
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.5, 0.5],
        c=60,
    )

    return ensemble_retriever

final_retriever = Indexing()

# TOOLS DECORATOR
@tool
async def search_docs(query: str)-> str:
    """
    A search tool that search the given corpus for user's query.
    Always provide the answer from the provided documents
    Use this when you need factual information from the material you've been provided.
    """
    global final_retriever
    try:
        result = await final_retriever.ainvoke(query)

        # chunks = []
        # for doc in result:
        #     chunks.append(doc.page_content)
        
        # Modern clean list comprehension combined with XML tagging
        formatted_chunks = [
            f"<document index='{i}'>\n{doc.page_content}\n</document>"
            for i, doc in enumerate(result)
        ]
        return "\n".join(formatted_chunks)
        # return "\n\n".join(chunks)
    except Exception as e:
        log.exception("search_docs retriever failed", error=str(e))
        raise

# AGENT CONFIGURATION
agent = create_agent(
    model=llm,
    tools=[search_docs],
    system_prompt= 
    """
    Role:You're an agent with external knowledge base with context.
         You always use your tool to retrieve data from external database when user ask context speciic question


    Constraints: Use the following pieces of retrieved context to answer the question. 
                 If you don't know the answer, just say that you don't know.
                 Do not produce wrong answer with confidence.

    Output_format: Accurate, Precise and Meaningful.
                   'strictly' Paraphrase, never quote directly
                   """
)

# MAIN RESPONSE HANDLER
@mcp.tool()
async def rag(query) -> str:
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
    @retry_with_backoff()
    async def response_func():
        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=query)]}
            )
        except ValueError as e:
            log.exception("rag agent invoke failed", error= str(e))
            raise

        final_response = result["messages"][-1]
        content = final_response.content
        if isinstance(content, list):
            return " ".join(block["text"] for block in content if block.get("type") == "text")
        return content

    return await response_func()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
