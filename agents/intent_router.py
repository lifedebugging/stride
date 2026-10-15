import re
import json
import unicodedata
import numpy as np
from typing import Any
import torch
from typing import List, Dict, Tuple
from pathlib import Path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from intent_registery import INTENT_REGISTRY
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from scipy.special import expit as sigmoid
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder
from logging_handler import get_logger
import time

log = get_logger("router logic")

"""
This is a json file used as a dataset
in semantic router
"""

CURRENT_DIR = Path(__file__).resolve().parent

MODEL_PATH = CURRENT_DIR / "semantic_registry.json"

with open(MODEL_PATH, 'r', encoding='utf-8') as file:
    semantic_dataset  = json.load(file)
    
# stopwords
"""
Here is used nltk corpus for stopwords removal
There contain some pre defined stopwords
"""
stop_words = set(stopwords.words('english'))

# embedding model
"""
HuggingFace embedding model is used for embedding vectors
"""
try:
    embeddings = HuggingFaceEmbeddings(
        model="all-MiniLM-L6-V2"
        )
    
except Exception as e:
    log.exception(f"HuggingFaceEmbedding model failure:{e}")
    
# encoder model
"""
A Cross encoder model used after retrieval as a scoring system
"""
try:
    encoder_model = CrossEncoder("BAAI/bge-reranker-v2-m3",
                                model_kwargs={"torch_dtype": torch.float32}) # BAAI/bge-reranker-v2-m3 OR all-MiniLM-L6-v2
except ValueError as e:
    log.exception(f"Cross Encoder model failed to load: {e}")

# document preparation for semantic router
"""
This is a document preparation process 
iterating over semantic dataset to create 'Document'
and storing in below variables
"""

documents = []

for item in semantic_dataset:
    category_name = item["name"]
    for example in item["positive_examples"]: 
        new_data = Document(
            page_content=example,
            metadata = {"category": category_name}
            )
        documents.append(new_data)
    
# vector store embeds building
"""
InMemoryVectorStore is a standard storage method 
uses ram for storage.
Builds the embedding stroage.
"""
try:
    vector_store = InMemoryVectorStore.from_documents(
        documents, 
        embeddings,
        )
except Exception as e:
    log.error("vector store build failed", error=str(e))

# retriever
"""
embeddings retriever using
as_retriever standard module for retrieving embeddings.
"""

embed_retriever = vector_store.as_retriever(k=10)


# filtering function for bm25 preprocess function
"""
Preporcess function created solely for used by bm25 retrievers
It filters the query string in various ways
such as lower casing, filtering out the stopwords
"""

def Preproccessing(query: str):
    # normalization
    normalized_uni_query = unicodedata.normalize('NFKC', query)
    # lower case
    tokens = word_tokenize(normalized_uni_query.lower())
    # filter
    filtered_tokens = [word for word in tokens if word.isalpha() and word not in stop_words]

    return filtered_tokens 

# bm25 document building
"""
bm25 retriever defined with k = 5 value.
and custom preprocess function
"""

bm25_retriever  = BM25Retriever.from_documents(
    documents,
    k = 10,
    preprocess_func=Preproccessing
    )

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, embed_retriever],
    weights=[0.3, 0.7],
    c=60,
)
    
# keyword router refined
"""
A keyword mapping function
goes through all the keywords in keyword_registry
append the category
"""

# def build_keyword_map():
#     keyword_map = {}
#     for category, data in INTENT_REGISTRY.items():
#         for keyword in data["keywords"]:
#             if  keyword in keyword_map:
#                 keyword_map[keyword].append(category)
#             else:
#                 keyword_map[keyword] = [category]
    
#     return keyword_map

# keyword_map = build_keyword_map()
"""
This calculates how many categories a keyword appears in.
"""    
# # IDf weight
# def compute_idf(keyword_map, N):
#     idf = {}
#     for keyword in keyword_map.items():
#         df = len(keyword_map[keyword])
#         idf[keyword] = math.log(N /df)
#     return idf
    
# N = len(INTENT_REGISTRY)
# idf = compute_idf(keyword_map, N)
    
# Filtering
"""
This is a filtering function similar to preprocessing function
However this one is requires to flat down query to keywords only
using the three different types of filteration method
the result of the is function will be used in keyword_intent
to calculate confidence"""

def filtering(query: str):

    # normalization
    normalized_uni_query = unicodedata.normalize('NFKC', query)
    # lower case
    tokens = word_tokenize(normalized_uni_query.lower())
    # filter
    filtered_tokens = [
        word for word in tokens 
        if word.isalpha() and word not in stop_words]
    
    # If the query is completely erased, return original tokens
    if not (len(filtered_tokens) == 0):
        log.debug(f"filtered tokens: {tokens}")
        return filtered_tokens
    
    log.debug(f"tokens: {tokens}")
    return tokens      
    #list required for counting meaningful words in denominator.
 
 #normalization    
def normalization(query : str):
    """
    Specifically to normalizer query that will be compared with keywords so to compare with keyword u need keywords
    hence 'stripping' query and using '.lower()' to turn all into lower case
    then use 're' to strip more than one repeated punctuation from the query 
    Example - amazing!! becoms amazing!
    and finally normalize it with 'NFKC' - Non formal KC
    compatibility decomposition and then applies canonical composition
    """
    
    stripped_query = query.lower().strip()
    dup_query = re.sub(r'([!?.,;:])\1+', r'\1', stripped_query)
    normalized_uni_query = unicodedata.normalize('NFKC', dup_query)
    
    return normalized_uni_query 

# test_norm = normalization("what's up")
# print(test_norm)
#keyword searching for intent
def keyword_intent(query : str, top_k: int=1)-> List[Dict]:
    """
    Classify a user query against the intent registry.
    
    Args:
    query: The user query string
    top_k: Number of top categories to return (default 1 for hard routing)
    
    Returns:
    List of dicts with category, confidence, model, priority, tools.
    Empty list if no match(fall through to LLM fallback).
    """ 
    user_query = normalization(query)
    filtered_token = filtering(query)
    
    #step 2 - scores for each directory
    scores = {} 
    
    #step 1 - The multi-keyword scan
    for category, data in INTENT_REGISTRY.items():
        matched = []
        
        score = []
        
        for keyword in data["keywords"]:
            
            if re.search(r'\b'  + re.escape(keyword) + r'\b', user_query):  #'\b' at the start and end make sure it match the exact keyword and re.escape is to automatically escape special characters/punctuation
                weight = len(keyword.split())
        
                score.append(weight)
                matched.append(keyword)
        """
        r'\bword\b': Matches the exact, standalone word.
        r'\bcat': Matches words starting with "cat" (e.g., catapult, cat).
        r'cat\b': Matches words ending with "cat" (e.g., wildcat, cat)."""
        
        """
         re.escape(string) is a function in the built-in re module used to 
         automatically escape special characters (like *, +, ?, ., ^, $, etc.) by adding a backslash (\) before them."""
        
                    
        # priority = int(data.get("priority", 5)) 
        # print(len(filtered_token))
        # if len(filtered_token) == 0:
            
        #     return []
        
        # Find the confidence
        confidence = sum(score) / len(filtered_token)        
        if confidence > 0.75:
            
            
            scores[category] = {
                    "category": category,
                    "confidence": round(min(confidence, 0.99), 2),
                    "model": data["model"],
                    "tool": data["tool"],
                }
        
    if not scores:
        log.warning(f"Keyword scores is empty")
        return []
    
    #sort by confidence descending
    sorted_scores = sorted(scores.values(), key=lambda x: x["confidence"], reverse=True)
    return sorted_scores[:top_k]

# test = keyword_intent("good morning")
# print(test)

# Map category names to their positive examples list
pos_lookup = {
        item["name"]: item["positive_examples"] for item in semantic_dataset
    }

# If your semantic_registry.json missing an explicit threshold key, fallback to a defaults 
normalized_threshold = {
        item["name"]: item.get("threshold", 0.34) for item in semantic_dataset
    }

# model and tool lookup  
keyitem_lookup = {item["name"]: {"model" : item["model"], "tool": item["tool"]} for item in semantic_dataset}

# texts = [ex for item in semantic_dataset for ex in item['positive_examples']]

# cats = [entry["name"] for entry in semantic_dataset for ex in entry["positive_examples"]]

examples = [(ex, entry["name"]) for entry in semantic_dataset for ex in entry["positive_examples"]]

texts = [t for t, _ in examples]  
cats  = [c for _, c in examples]   

        

emb_matrix = np.array(embeddings.embed_documents(texts))
emb_matrix /= np.linalg.norm(emb_matrix, axis=1, keepdims=True) 
cat_array = np.array(cats)

GAP_MIN = 0.20   # starting guess for MiniLM cosines — replace with calibrated value

indices_by_category = {c: np.where(cat_array == c)[0] for c in set(cats)}

def semantic_res(best_cat, best_score) -> List[Dict[str, Any]]:
    category, score = best_cat, best_score
    
    if not category:
        return []
    
    lookup = keyitem_lookup[best_cat]
    return [{
        "category": category,
        "confidence": score,
        "model": lookup.get("model", "fast"),
        "tool": lookup.get("tool")
    }]
  
def stage2_rerank(query: str, sims: np.ndarray, ranked) -> List[Dict[str, Any]]:
    """
    Ambiguous case only: rerank top-3 examples of the top-2 categories — 6 pairs, not 75.
    """
    top2 = [c for c, _ in ranked]

    pairs, pair_cats = [], []
    for c in top2:
        idx = np.where(cat_array == c)[0]
        top3 = idx[np.argsort(sims[idx])[::-1][:3]]   # category's 3 best examples by Stage-1 cosine
        for i in top3:
            pairs.append([query, texts[i]])
            pair_cats.append(c)
    
    start = time.perf_counter()        
    rerank_scores = encoder_model.predict(pairs)   # your existing model, logit scale
    
    end = time.perf_counter()
    duration = end - start
    log.debug(f"execution time stage2: {duration:.2f}seconds")
    
    per_cat = {c: float(np.mean([s for s, 
                                 pc in zip(rerank_scores, 
                                           pair_cats) if pc == c])) for c in top2}
    ranked2 = sorted(per_cat.items(), key=lambda x: -x[1])
    
    log.debug(f"ranked 2 : {ranked2}")
    top_cat, top_score = ranked2[0]
    _ , second_score = ranked2[1]
    
    gap = top_score - second_score

    # YOUR existing numbers — same scorer, same scale as your current code
    if top_score >= normalized_threshold[top_score] and gap >= GAP_MIN:
        return semantic_res(top_cat, top_score)
    return []   # genuinely ambiguous → escalates to LLM/agent downstream
    
def semantic_intent(query: str) -> List[Dict]:
    
    q = np.array(embeddings.embed_query(query))
    q /= np.linalg.norm(q)
    
    sims = emb_matrix @ q
    
    per_cat = {}
    # stage1_rank 
    for c, idx in indices_by_category.items():
        per_cat[c] = float(np.mean(np.sort(sims[idx])[::-1][:3]))
        
    start = time.perf_counter()     
    ranked = sorted(per_cat.items(), key=lambda x: -x[1])
    end = time.perf_counter()
    
    duration = end - start
    log.debug(f"execution time stage1: {duration:.2f}seconds")
    
    log.debug(f"ranked 1 {ranked}")
    best_cat, best_score = ranked[0]
    _ , second_score = ranked[1]
    gap = best_score - second_score

    
    if best_score > normalized_threshold[best_cat] and gap >= GAP_MIN:
        return semantic_res(best_cat, best_score)
    
    return stage2_rerank(query, sims, ranked[:2])
  
    # try:
    #     results = ensemble_retriever.invoke(query)
    # except Exception as e:
    #     log.exception("ensemble retriever failed to retreive documents", error=str(e))
    
    # if not results:
    #     return []
    
    
    # # Track distinct categories returned by the retriever
    # retrieved_categories = list(
    #     set([item.metadata["category"] for item in results])
    # )
    
    # #score list -> [category, score of that category]
    # category_scores = []
    #  #temp list to save all 25 score to use top k mean later
    
    # # Tracks which pair belongs to which category downstream

    # for category in retrieved_categories:
    #     # Resets variable state on every loop iteration
        
    #     lookup_examples = pos_lookup.get(category, [])
        
    #     if not lookup_examples:
    #         continue
    #     # looping over lookup which is [positive example] and scoring query per example.
    #     # Constructing pairs for optimized matrix prediction speed
        
    #     # pairs = [[query, text_example] for text_example in lookup_examples]
        
    #     # Batch predict all phrase pairs at once
    #     raw_scores = encoder_model.predict(pairs) 
    #     raw_scores = np.array(raw_scores, dtype=np.float32)
        
    #     # Sort and average the top 3 strongest matches
    #     sorted_scores = sorted(raw_scores, reverse=True)
    #     top_k_avg = np.mean(sorted_scores[:3])
    #     category_scores.append(
    #         {"category": category,
    #          "confidence": float(top_k_avg)
    #          })  

    # # Sort categories by best score descending
    # category_scores.sort(key=lambda x: x["confidence"], reverse=True)

    # if not category_scores:
    #     return []

    # raw_scores = np.array([float(s["confidence"]) for s in category_scores], dtype=np.float32)
    # names = np.array([s["category"] for s in category_scores])
    # #applying sigmoid funcition
    # # confidence = sigmoid(raw_scores)
    # # round_confidence = np.round(confidence, 2)
    # # zipped = zip(names, round_confidence)
    # round_confidence = np.round(raw_scores, 2)
    # zipper = list(zip(names, round_confidence))
    
    # best_category, best_score = zipper[0]
    # target_threshold = normalized_threshold.get(best_category, 0.00)


    # if not (len(zipper) > 1):
    #     gap = 0.99
    
    # gap =round(best_score - zipper[1][1], 2)
  
    # lookup = keyitem_lookup[best_category]
      
    # winner = []
    # # Adjust these values based on scores
    # if (not best_score > target_threshold) and (not gap >= 0.30):
    #     return []
    
    # winner.append({
    #     "category": best_category,
    #     "confidence": float(best_score),
    #     "margin_gap": float(gap),
    #     "model": lookup["model"],
    #     "tool": lookup["tool"]
    # })
    
    # return winner


    

