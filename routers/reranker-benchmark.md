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

TinyBert is 4.39 M parameter cross encoder, it has two transofrmers layer and the total memory it uses is 22.5 MB with process after embedding model.
It delivers cross encoder accuracy with a fraction of the memory and computer of heavier alternatives

```
{"event": "Memory checkpoint: after imports, before models: 526.7 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:08.791881Z"}
{"event": "Memory checkpoint: after MiniLM embedding model: 636.3 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:12.591460Z"}
{"event": "Memory checkpoint: after MiniLM-L2 cross-encoder reranker: 713.5 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:39.298048Z"}
{"event": "Memory checkpoint: after vector store: 766.1 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:12:52.836170Z"}
{"event": "Memory checkpoint: after embedding matrix: 787.1 MB RSS", "filename": "intent_router.py", "func_name": "memory_checkpoint", "lineno": 31, "level": "info", "timestamp": "2026-11-26T20:13:10.858224Z"}
```

Where as MiniLM-L2 cross encoder memory size is 77.2 MB with process after embedding model 
