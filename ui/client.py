import requests
from config.logging_handler import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import time
import uuid
import json

app = FastAPI ()

thread_id = uuid.uuid4()
thread_id_str = str(thread_id)

log = get_logger("client.response")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8001/route"],  # Your web app's URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Define the exact shape of the data you expect from TypeScript
class ChatRequest(BaseModel):
    query: str
    thread_id: str

class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    
    user_text = request.query
    thread_id = request.thread_id

    # POST to x
    try: 
        response = requests.post(url="http://127.0.0.1:8001/route", json=user_text, stream=True)
        response.raise_for_status()
    
    except Exception as e:
        log.exception(f"client POST failed, check url: {e}")
        raise
        
    try:
        start = time.perf_counter()
        #iter_lines change iter_content
        for chunk in response.iter_content(chunk_size=1024):
            if not chunk:
                break
            
            yield chunk.decode()
            time.sleep(0.04)  # 40ms delay between chunks for natural feel
                
        elapsed = (time.perf_counter() - start)
        print()
        log.info(f"response complete, {elapsed:.2f}")
        print()  #newline after response completes
        
    except Exception as e:
        log.exception(f"response interrupted: {e}")
        raise
    
    StreamingResponse(chat_endpoint(user_text), media_type="text/plain")
       
    
#parse response
#final_response = response.json()["answer"]
#no .json(). It's raw text chunks now.
    #print answer
    
#iter_lines() returns bytes by default.

    