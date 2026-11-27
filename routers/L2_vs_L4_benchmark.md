# L4
```
{"event": "Memory checkpoint: after imports, before models: 521.7 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:52:46.556337Z"}
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 620.50it/s]
{"event": "Memory checkpoint: after MiniLM embedding model: 629.9 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:52:50.918657Z"}
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████| 73/73 [00:00<00:00, 1043.74it/s]
{"event": "Memory checkpoint: after MiniLM-L4 cross-encoder reranker: 708.9 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:52:52.602035Z"}
{"event": "Memory checkpoint: after vector store: 761.0 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:53:06.538665Z"}
{"event": "Memory checkpoint: after embedding matrix: 783.6 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:53:20.253825Z"}
```

The memory foot print of `L4` is `708.9MB` after import so that's a solid `70 MB` after embedding model

# L2
```
{"event": "Memory checkpoint: after imports, before models: 522.4 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:19:09.441722Z"}
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 1269.38it/s]
{"event": "Memory checkpoint: after MiniLM embedding model: 631.4 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:19:13.700371Z"}
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████| 41/41 [00:00<00:00, 13688.33it/s]
{"event": "Memory checkpoint: after MiniLM-L2 cross-encoder reranker: 697.4 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:19:15.463020Z"}
{"event": "Memory checkpoint: after vector store: 749.5 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:19:26.714220Z"}
{"event": "Memory checkpoint: after embedding matrix: 771.7 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-27T10:19:39.528019Z"}
````
Memory footprint of `L2` is `697.4 MB` after import and that's a `66 MB` after embedding model

# comparison
```
Model    Memory
L2       66MB
L4       70MB
```

# But what is the performance difference?

On the sentence Transformers model card’s benchmarks, MiniLM-L4-v2 ranks better, but is slower than L2-v2:
```
Model	              TREC DL 2019 NDCG@10	  MS MARCO Dev MRR@10	 Docs/sec
MiniLM-L2-v2	      71.01	                  34.85                4,100
MiniLM-L4-v2	      73.04	                  37.70	               2,500
```
That’s `+2.03 NDCG` points and `+2.85 MRR `points for `L4`, with about `39% lower` throughput in the card’s test. Throughput was measured on a `V100 GPU`

SO I gotta measure on my own separately, but since my ranker scores only about six pairs and only run on ambugious queries, the lattency difference may be small

