from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dataclasses import dataclass
from dotenv import load_dotenv
from config.logging_handler import setup_logging, get_logger
from enum import Enum
from pydantic import SecretStr
from pydantic_settings import BaseSettings 
from typing import Optional, Any
import os

load_dotenv()
#logger instantiation
logger = setup_logging("INFO")
log = get_logger("model configuration")

# Model
class ModelTier(Enum):
    """The two model tier available in the stride """
    fast = "Fast"
    smart = "Smart"


# config
class LLMConfig(BaseSettings):
    groq_api_key: Optional[SecretStr] = None
    gemini_api_key: Optional[SecretStr] = None
    
    class CaseConfig:
        case_sensitive=False
        
keys = LLMConfig()
@dataclass
class ModelConfig:
    model_name: str
    temperature: float
    max_tokens: int = 4096
    
MODEL_MAP = {
    ModelTier.fast: ModelConfig(
        model_name= "gemini-3.5-flash-lite",
        temperature= 0.6,
        # max_tokens=4096
    ),
    ModelTier.smart: ModelConfig(
        model_name= "openai/gpt-oss-120b",
        temperature= 1.0,
        # max_tokens=4096
    ),
    
}


def log_routing_decision(decision: dict) -> ModelTier:
    """Log the routing decision and return its model tier."""
    
    category = decision["category"]
    confidence = decision["confidence"]
    model_tier_str = decision["model"]
    tools = decision.get("tool", "None")
    
    try:
        tier = ModelTier(model_tier_str)
    except ValueError:
        log.exception(
            "unknown model tier",
            category=category,
            model_tier=model_tier_str,
        )
        raise
    
    config = MODEL_MAP[tier]
    routing_fields = {
        "category": category,
        "confidence": confidence,
        "model_tier": tier.value,
        "model_id": config.model_name,
        "tools": tools,
    }

    log.info("routing decision", **routing_fields)
    return tier


def model_endpoint(tier):
    config = MODEL_MAP[tier]

    if tier == ModelTier.fast:
        gemini_model = ChatGoogleGenerativeAI(
            model=config.model_name,
            api_key=keys.gemini_api_key,
            # base_url="https://generativelanguage.googleapis.com/v1beta/openai/" ,
            #temperature=config.temperature,
        )
        
        try:
            return gemini_model
        except Exception as e:
            log.exception(
                f"failed to load Gemini model, error: {e}")
        # i want to put here where it fallback to smaller llm if above fails
    
    if tier == ModelTier.smart:
        groq_model = ChatOpenAI(
            model=config.model_name,
            api_key=keys.groq_api_key,
            base_url="https://api.groq.com/openai/v2",
            temperature=config.temperature
        )
        
        try:
            return groq_model
        except Exception as e:
                log.exception(
                    f"failed to load Groq model, error: {e}")
    # if this model fail flalback to fast 
     
    
CLASSIFIER_CONFIG = ModelConfig(
    model_name="openai/gpt-oss-20b",
    temperature=0.0
)
 
def classifier_endpoint():
    classifier_model = ChatOpenAI(
        model=CLASSIFIER_CONFIG.model_name,
        api_key=keys.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=CLASSIFIER_CONFIG.temperature
    )
    
    try:
        return classifier_model
    except Exception as e:
        log.exception(
            f"failed to load classifier model, error: {e}")
