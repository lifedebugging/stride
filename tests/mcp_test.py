import os
import sys
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from nltk.tokenize import word_tokenize
from error_handler import retry_with_backoff
from mcp.server.fastmcp import FastMCP

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
load_dotenv(override=True)
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

mcp = FastMCP("rag_subagent")
final_retriever = None

llm = ChatOpenAI(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0
)

def build_retrievers(vector_store, splitted_documents):
    bm25_retriever = BM25Retriever.from_documents(
        splitted_documents, k=2, preprocess_func=word_tokenize)
    chroma_retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 2})
    return EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.5, 0.5], c=60)

def Indexing():
    loader = PyPDFLoader(
        file_path="D:/Downloads/eit-digital-artificial-intelligence-report.pdf",
        mode="single", extract_images=False, extraction_mode="layout")
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4", chunk_size=500, chunk_overlap=50)
    splitted_documents = splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
    vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory="D:/Downloads/")
    if not os.path.exists("D:/Downloads/chroma.sqlite3"):
        vector_store.add_documents(documents=splitted_documents)
    return build_retrievers(vector_store, splitted_documents)

@tool
async def search_docs(query: str) -> str:
    """Search AI documentation for factual information."""
    global final_retriever
    try:
        if final_retriever is None:
            final_retriever = Indexing()
        result = await final_retriever.ainvoke(query)
        return "\n\n".join(doc.page_content for doc in result)
    except Exception as e:
        return f"error: {e}"

agent = create_agent(
    model=llm,
    tools=[search_docs],
    system_prompt="""You are a sub-agent with access to an AI documentation knowledge base.
Use the search tool for document-specific questions.
For general questions answer directly.
Always paraphrase, never quote directly.
Be precise and accurate.""")

@mcp.tool()
async def rag_query(query: str) -> str:
    """Search AI documentation and return precise answers. Use for document-specific questions about AI."""
    @retry_with_backoff()
    async def response_func():
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=query)]})
        return response["messages"][-1].content
    return await response_func()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")