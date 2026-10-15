import requests
from logging_handler import get_logger
from datetime import datetime
import time
import uuid
import json

thread_id = uuid.uuid4()
thread_id_str = str(thread_id)

log = get_logger("client.response")

def ClientChunks():
    while True:
        #input
        query = {
            "query": input("\n\nprompt: "),
            "thread_id": thread_id_str
            }
        
        if query["query"] == "exit":
            break

        # POST to x
        try: 
            response = requests.post(url="http://127.0.0.1:8001/route", json=query, stream=True)
            response.raise_for_status()
        
        except Exception as e:
            log.exception(f"client POST failed, check url: {e}")
            
        try:
            start = time.perf_counter()
            #iter_lines change iter_content
            for chunk in response.iter_content(decode_unicode=True, chunk_size=None):
                if not chunk:
                    return "No response found"
                
                print(chunk, end="", flush=True)
                time.sleep(0.04)  # 40ms delay between chunks for natural feel
                    
            end = (time.perf_counter() - start)
            print()
            log.info(f"response complete, {end:.2f}")
            print()  #newline after response completes
            
        except Exception as e:
            log.error(f"response interrupted: {e}")
            
client = ClientChunks()            
    
#parse response
#final_response = response.json()["answer"]
#no .json(). It's raw text chunks now.
    #print answer
    
#iter_lines() returns bytes by default.

    