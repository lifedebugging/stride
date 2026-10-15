import asyncio
from dataclasses import dataclass, asdict
from intent_router import normalization, keyword_intent, semantic_intent
from _init_ import get_ctx, AppStateContext
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from model_config import classifier_endpoint
from logging_handler import get_logger

log = get_logger("decision_logic")

class QueryLength(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class StrictOutput(BaseModel):
    category: str = Field(default="uncategorized-classifier", description="Intent category like GREETINGS, CODING, etc.")
    confidence: float = Field(default=0.0, description="Confidence score between 0 and 1")
    model: Literal["Fast", "Smart"] = Field(default="Fast", description="Model tier: Fast for simple queries, Smart for complex")
    tool: str = Field(default="None", description="Invoke 'get_time' for time queries, 'rag_subagent' for external documents related to 'How Organizations Use AI: Evidence from ChatGPT', or return 'none' if no tool is needed.")
    
    
@dataclass
class IntentResult:
    category: str
    confidence : float
    model : str
    tool : str
    source : str    
    
    
def classify_query_length(query : str) -> QueryLength:
    words = len(query.split())
    if not words <=10:
        return QueryLength.MEDIUM
    if not words <= 50:
        return QueryLength.LONG
    return QueryLength.SHORT
    


async def safe_llm_classifier(query : str, 
                              timeout : float = 3.0
                              ) -> StrictOutput:
    try:
        llm_classifier = classifier_endpoint().with_structured_output(StrictOutput)
        
        return await asyncio.wait_for(
            llm_classifier.ainvoke(query),
            timeout = timeout)
        
    except asyncio.TimeoutError:
        log.info(f"LLM classification timed out after {timeout}s for query: '{query}'")
        return StrictOutput(model="Fast", tool="None")
    
    except Exception as e:
        log.exception(f"Classifier failed: {e}")
        return StrictOutput(model="Fast", tool="None")
        
        
async def resolve_intent(
    query : str,
    keyword_results : Optional[List[Dict[str, Any]]],
    semantic_results : Optional[List[Dict[str, Any]]],
    length_tier : QueryLength,
    ctx : Any
) -> IntentResult:
    
    if length_tier == QueryLength.SHORT:
        
        if not keyword_results :
            log.error("Keyword result is empty")
            return _fallback(ctx)
            
        return _pack(keyword_results[0], "keyword")
        # future change : add the timeout for both the keyword and semantic if taking too long to answer less than 3.0 sec
        # elif semantic_results and semantic_results[0].get("confidence", 0.0) >= 0.34: 
        #     return _pack(semantic_results[0], "semantic")
       
    
    if length_tier == QueryLength.MEDIUM:
        if not semantic_results :
            log.info("Semantic result is empty initiating fallback to Classifier")
            classifier_result = await safe_llm_classifier(query)
            
            if not classifier_result:
                log.info("classifier result is empty during Semantic fallback")
                return _fallback(ctx)
                
            return _pack(classifier_result.model_dump(), "llm")
            
        return _pack(semantic_results[0], "semantic")
        

    if length_tier == QueryLength.LONG:
        classifier_result = await safe_llm_classifier(query)
        
        if not classifier_result:
            log.info("classifier result is empty")
            return _fallback(ctx)
        
        try:
            return asdict(_pack(classifier_result.model_dump(), "llm"))
        except Exception as e:
            return f"classifier failed to fetch intent: {e}"
        
        
    
    
def _pack(raw: Dict[str, Any],
          source: str
          ) -> IntentResult:
    
    return IntentResult(
        category= raw.get("category", "uncategorized"),
        confidence=float(raw.get("confidence", 0.0)),
        model=raw.get("model", "Fast"),
        tool=raw.get("tool", "None"),
        source=source
    )


def _fallback(ctx: Any) -> IntentResult:
    """Guaranteed safe fallback state"""
    return IntentResult(
        category="fallback",
        confidence=0.0,
        model="Fast",
        tool="None",
        source="fallback"
    )

def predict_language(text: str, 
                     ctx: AppStateContext, 
                     k: int = 1
                     ):
    
    model = ctx.lang_model
    label, prob = model.predict(text, k)
    return [l.replace("__label__", "") for l in label]


async def IntentCall(func : callable, 
                                   *args, 
                                   timeout,
                                   log_label = None,
                                   ):
            
            if not log_label :
                log_label = func.__name__    
                
                        
            try:
                results = await asyncio.wait_for(
                    asyncio.to_thread(func, *args),
                    timeout=timeout
                    )
                print(results)
                return results
                
            except asyncio.TimeoutError:
                log.exception(f"{log_label} intent timed out", timeout=timeout)
                return None
            
            except Exception as e:
                log.exception(f"{log_label} failed: {e}")
                return None

async def Decision_logic(query: str,
                         ctx: Any
                        ) -> Dict[str, Any]:
    
    
    try:
        raw_query = query
        normalized = normalization(raw_query)

        try:
            lang_results = predict_language(normalized, ctx)
            lang = lang_results[0]
            
            if "en" not in lang:
                log.info("Not an English")
                return asdict(_fallback(ctx))
            
        except Exception as e:
            log.error(f"Language detection failed, proceeding as English. Error : {e}")
            
        length_tier = classify_query_length(normalized)
        
        keyword_results, semantic_results = None, None
        
        # Check the length tier to conditionally invoke the correct intent
        if length_tier == QueryLength.SHORT:
            keyword_results = await IntentCall(
                keyword_intent, normalized, timeout=1.5
            )
            
            semantic_results = None  # Or skip entirely depending on your needs
        elif length_tier == QueryLength.MEDIUM:
            semantic_results = await IntentCall(
                semantic_intent, normalized, timeout=30.0
            )
        
  
        result = await resolve_intent(
            query=normalized,
            keyword_results = keyword_results,
            #check what keyword_results return for knowing what it actually return similarly semantic
            semantic_results = semantic_results,
            # why length_tier here is being calculated then it again returning by reslove intent as QueryLength
            length_tier=length_tier,
            ctx=ctx,
        )
        # where is even result is being used?
        
        return asdict(result)
 
    except Exception as e:
        log.exception(f"catastrophic failure in decision logic: {e}")
        return asdict(_fallback(ctx))
        

