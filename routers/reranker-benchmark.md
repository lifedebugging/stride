# BENCHMARK
```
{'intent': 'GREETINGS', 'name': 'Greetings & Salutations', 'model': 'Fast', 'tool': None, 'priority': 1, 'match': 'hey', 'exact': False}
{"event": "Memory checkpoint: after imports, before models: 527.1 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:16:11.606392Z"}
Loading weights: 100%|███████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 846.43it/s]
{"event": "Memory checkpoint: after MiniLM embedding model: 633.5 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:16:15.831384Z"}
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████| 41/41 [00:00<?, ?it/s]
{"event": "Memory checkpoint: after TinyBERT reranker: 655.0 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:16:17.151789Z"}
{"event": "Memory checkpoint: after vector store: 707.5 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:16:33.557342Z"}
{"event": "Memory checkpoint: after embedding matrix: 728.8 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:16:50.707297Z"}
INFO:     Started server process [13880]
INFO:     Waiting for application startup.
```
This is the raw data from the terminal

TinyBert is 4.39 M parameter cross encoder, it has two transofrmers layer and the total memory it uses is `22.5 MB` with process after embedding model.
It delivers cross encoder accuracy with a fraction of the memory and computer of heavier alternatives

```
{"event": "Memory checkpoint: after imports, before models: 526.7 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:08.791881Z"}
{"event": "Memory checkpoint: after MiniLM embedding model: 636.3 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:12.591460Z"}
{"event": "Memory checkpoint: after MiniLM-L2 cross-encoder reranker: 713.5 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:39.298048Z"}
{"event": "Memory checkpoint: after vector store: 766.1 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:52.836170Z"}
{"event": "Memory checkpoint: after embedding matrix: 787.1 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:13:10.858224Z"}
```

Where as MiniLM-L2 cross encoder memory size is `77.2 MB` with process after embedding model 

```
{"event": "Memory checkpoint: after imports, before models: 522.8 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T09:51:27.576035Z"}
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 552.25it/s]
{"event": "Memory checkpoint: after MiniLM embedding model: 632.2 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T09:51:31.665971Z"}
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 393/393 [00:10<00:00, 37.19it/s]
{"event": "Memory checkpoint: after BGE reranker: 2712.3 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T09:52:47.588965Z"}
{"event": "Memory checkpoint: after vector store: 2689.7 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T09:53:02.043420Z"}
{"event": "Memory checkpoint: after embedding matrix: 2710.3 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T09:53:15.825786Z"}
```

Above is the memory footprint of a Bge ranker - real heavy 2712.3 MB that after re ranker that a difference of `2080.1 MB`
however what I found weird is that memory dropped to `2689 MB` after the ranker and the reason upon searching Is *temporary* load buffers or earlier work probably released
so could be that.

Below is the representation of all model compared I will be sharing the spreadsheet as well 

```
Checkpoint Stage	           TinyBERT Run	         MiniLM-L2 Run	         BGE Reranker Run	
After imports (pre-models)	    —	                522.4 MB	               522.8 MB	
After MiniLM embedding	        —	                631.4 MB (+109.0 MB)	   632.2 MB (+109.4 MB)	
After reranker load	         646.2 MB	            697.4 MB (+66.0 MB)	     2,712.3 MB (+2,080.1 MB)	
After vector store	         698.9 MB (+52.7 MB)	749.5 MB (+52.1 MB)	     2,689.7 MB (-22.6 MB)	
After embedding matrix	     708.5 MB (+9.6 MB)	  771.7 MB (+22.2 MB)	     2,710.3 MB (+20.6 MB)	
```

What it tells me:
1. `BGE reranker` is the main memory bottleneck adding roughly `2.08 GB` at load time pushing the full pipeline near `2.7 GB` and taking ~ `15-20 seconds` just on weight loading
2. `MiniLM-L2` and `TinyBERT` is under `800 MB` (I tested twice) building roughly upto `750 MB`

My final decision is that BGE re ranker does not add up more `+` then `-` at least for my system
Only `+` are its more precise, the chances of semantic router downstreaming query that is **IN** or **Matches** the registry would be significantly low however that's only when the query does matches in registry and the *stage 1* misses it.

Which is again pretty low because ever since I am started using `np.max()` instead of taking `mean()` of the result most of the query get caught in `stage 1` 

That said `stage2` is just a safety net.

# conclusion
SO I will be using `MiniLM-L2` it has significantly less memory foot print, fast start up, cross encoder ability in under `100 MB` which will allow me to expand my search for free hosting service

**NOTE**: HOWEVER KEEP IN MIND THIS IS A MEMORY FOOTPRINT AFTER FIRST START UP NOT AFTER THE FIRST TIME CROSS ENCODER TACKLE THE QUERY THE RESULT MAY VARY

# changes

I will also be measuring how much **percentage** of query actually get downstream in all three cross encoders and compare the results.
