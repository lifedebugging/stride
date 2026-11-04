

# 8/15/ 26  Observation and problem behavioral test


input : hey

en

QueryLength.SHORT

0.99

{"category": "GREETINGS", "confidence": 0.99, "model\_tier": "Fast", "model\_id": "gemini-3.5-flash-lite", "tools": null, "event": "routing decision", "filename": "model\_config.py", "func\_name": "log\_routing\_decision", "lineno": 70, "level": "info", "timestamp": "2026-08-15T07:57:22.064821Z"}



triggers deterministic router

gets the response



input: what's up

triggers keyword \& semantic

however always overridden and answered by semantic response even though deterministic router has perfect match why?

efficiency : very slow

possibilities of having the keyword in deterministic router : very high

currently: keyword router timed out 

reason: before possible low score? now timed out?



problem: 

1\. why low score if the keyword in deterministic dictionary?

2\. Semantic should not be trigger at all if deterministic router

3\. keyword router should not be timeout at all if the score is low \~ skip (similarly for semantic intent) Done

4\. keyword router timed out fallback to semantic or fallback to llm? LLM seems plausible because it would be waste of       resource and latency if deterministic itself takes a lot of time. (It shouldn't)

5\. how to trigger external document questions more seamlessly (without querying every times : answer from document)? Done

6\. keyword and semantic running on different thread make them unstoppable having waste of cpu resources plus thread engaged even if program were to fail what's the solution?





# observation:



prompt: what's good

en

QueryLength.SHORT

````````````````here````````````````````````````````````

2026-08-15 13:57:08.626588

{"event": "keyword intent timed out", "filename": "decision\_logic.py", "func\_name": "Decision\_logic", "lineno": 189, "level": "error", "timestamp": "2026-08-15T08:27:23.494139Z"}

{"category": "uncategorized", "confidence": 0.0, "model\_tier": "Fast", "model\_id": "gemini-3.5-flash-lite", "tools": \["StructuredTool(name='get\_datetime', description='Returns current date and time with accuracy', args\_schema={'types': 'object', 'properties': {}}, response\_format='content\_and\_artifact', coroutine=<function convert\_mcp\_tool\_to\_langchain\_tool.<locals>.call\_tool at 0x0000019B75AB9440>)", "StructuredTool(name='rag', description='\\\\n    High performing sub agent retrieval augmented generator.\\\\n    Provide clean response for main agent.\\\\n    Provide precise answer with no gibberish.\\\\n    Never ask questions.\\\\n\\\\n    Args:\\\\n        query: The user query string\\\\n\\\\n    Returns:\\\\n        The final response of agent.\\\\n    ', args\_schema={'properties': {'query': {'title': 'query', 'type': 'string'}}, 'required': \['query'], 'title': 'ragArguments', 'type': 'object'}, response\_format='content\_and\_artifact', coroutine=<function convert\_mcp\_tool\_to\_langchain\_tool.<locals>.call\_tool at 0x0000019B75ABA3E0>)"], "event": "routing decision", "filename": "model\_config.py", "func\_name": "log\_routing\_decision", "lineno": 70, "level": "info", "timestamp": "2026-08-15T08:27:23.494139Z"}

2026-08-15 13:57:50.176628

Winner: Social Pleasantries \& Chitchat | Score: 0.86 | Gap: 99.0



what's good matches straight up 99% in deterministic but why do I not see the keyword intent score I print



question: 



is keyword not being triggered at all?

if not triggered at all then why timed out?

if an router is not being triggered it shouldn't timed out, it conflicts





# observation:



Tried another

input and its resonse:



prompt: goodbye

see ya. try not to get lost in the real world, it lacks a search bar.

2026-08-15 14:01:21 \[info     ] response complete              latency\_seconds=16.457095



behavior:

en

QueryLength.SHORT

2026-08-15 14:01:05.605207

{"event": "keyword intent timed out", "filename": "decision\_logic.py", "func\_name": "Decision\_logic", "lineno": 189, "level": "error", "timestamp": "2026-08-15T08:31:20.429664Z"}



keyword intent score logic skipped again?

Does it has something to do with registry? For example only first dict is being triggered?



# observation:

prompt: howdy

howdy. saddle up, what are we analyzing today?

2026-08-15 14:05:48 \[info     ] response complete              latency\_seconds=1.324914



en

QueryLength.SHORT

0.99

{"category": "GREETINGS", "confidence": 0.99, "model\_tier": "Fast", "model\_id": "gemini-3.5-flash-lite", "tools": null, "event": "routing decision", "filename": "model\_config.py", "func\_name": "log\_routing\_decision", "lineno": 70, "level": "info", "timestamp": "2026-08-15T08:35:47.075372Z"}



"howdy" belongs to \*\*first\*\* list, Is this the problem?



# Observation:

There it is

prompt: goodbye

en

QueryLength.SHORT

\[]

2026-08-15 14:20:54.348155

{"event": "keyword intent timed out", "filename": "decision\_logic.py", "func\_name": "Decision\_logic", "lineno": 189, "level": "error", "timestamp": "2026-08-15T08:51:09.234709Z"}



# important:

it's empty the keyword result itself is empty for some reason

hence timeout hence only semantic


8/16/26

we already have `confidence >= 0.70:` in `intent_router.py` so why `decision_logic.py` has

`if keyword_results and keyword_results[0].get("confidence") >= 0.8:` are they different or doing the same thing?


# Observation:

Bug founded upon printing number of variables and end points

I found that in here ` for category, data in INTENT_REGISTRY.items():`

it only scan the first category and skip the rest hence everything else that is **NOT** in first category
get's blank list and cause the keyword intent to skip.

For some reason the loop is not looping after first *turn*.


# observation

8/18/26

All the error traced back to keyword_intent underlying logic

the
```
sorted_scores = sorted(scores.values(), key=lambda x: x["confidence"], reverse=True)
    return sorted_scores[:top_k]
```
Was inaise the first loop hence ending pre maturely

keyword intent seems to be working correctly now

note: still imporper behavior for some keywords like *what's up* or *what up*

rest is working fine that's one problem solved.

question: is there anyways to that when tools are called to bypass/avoid the long process routers?



# observation

8/21

"what's up" or "what up" get empty list from `filtered tokens`

cause? 

**unkown**

prove:
```
user_query: {user_query}
 filtered token: []
 ```

two separate hypotheses now (isalpha() failing, or stop_words catching things)

Line by line: filtering

Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 2679.37it/s]
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 393/393 [00:23<00:00, 16.77it/s]
['w']
(project_venv) PS D:\Documents\Project_x> & d:\Documents\project_venv\Scripts\python.exe "d:/Documents/Project_x/x v5/intent_router.py"
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 2722.65it/s]
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 393/393 [00:22<00:00, 17.84it/s]
['wh']
(project_venv) PS D:\Documents\Project_x> & d:\Documents\project_venv\Scripts\python.exe "d:/Documents/Project_x/x v5/intent_router.py"
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 3148.12it/s]
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 393/393 [00:12<00:00, 31.47it/s]
['wha']
(project_venv) PS D:\Documents\Project_x> d:\Documents\project_venv\Scripts\python.exe "d:/Documents/Project_x/x v5/intent_router.py"
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 3363.15it/s]
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 393/393 [00:11<00:00, 34.69it/s]
[]
(project_venv) PS D:\Documents\Project_x> & d:\Documents\project_venv\Scripts\python.exe "d:/Documents/Project_x/x v5/intent_router.py"
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 3219.89it/s]
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 393/393 [00:15<00:00, 24.83it/s]
[]

Note : It goes empty list in "what" and "up" separately

More observation:

words like "when" and "why" continue to output empty list from `filtering`

test complete: stop is the culprit: where


# observation
8/22

the big question is what am i gonna do about culprit now,
option a: remove the culprit, confidence score break
option b: keep the culprit, an let things be as it is
option c: replace the culprit and find anther way to calculate confidence

But how am I planning to calculate confidence?

Exact/ fuzzy matching out of option. (already used it and no good for scalling)


First of all what is the problem here?

The stop words suppress the one and two word query as noise. hence empty list breaking the keyword intent.

The real solution is to somehow prevent this from happening

what is stopwords anyway?

Extremely common words such as the, this, is , at, that,

but why remove this?

It allow to only focus on keywords. IN keyword intent keywords matter the most.
saves time as well.

SO..

The best practice is to check if removing stop words empties your query. 
If it does, fall back to the original tokens so the application still has text to process.

# observation
24/8

Continuation of previous observation

today applied fix 1:

the fix is very simple
```
 if len(filtered_tokens) == 0:
        return tokens
```
Basiclally if the filtered token is empty just use the raw token

having something to compare is better have nothing and getting "keyword" router failed.

I m gonna run the code now and see how it holds.

Take a look at this:
```
what's up
what's up
en
what's up
what's up
user_query: what's up
 filtered token: ['what', "'s", 'up']
0.6666666666666666
0.0
0.0
0.0
0.6666666666666666
0.0
0.0
2026-08-24 12:57:56.208567
{"event": "keyword intent timed out", "filename": "decision_logic.py", "func_name": "Decision_logic", "lineno": 187, "level": "error", "timestamp": "2026-08-24T07:28:11.113674Z"}

```
Due to NFKC
the *s* after apostrophy get's separated and the confidence is being altered

is this a bug? does it hurt my output or intent?

second:
the previous **empty** filtered token is now fixed
```
what up
what up
en
what up
what up
user_query: what up
 filtered token: ['what', 'up']
0.0
0.0
0.0
0.0
1.0
0.0
0.0
{"category": "CASUAL_TALK", "confidence": 0.99, "model_tier": "Fast", "model_id": "gemini-3.5-flash-lite", "tools": null, "event": "routing decision", "filename": "model_config.py", "func_name": "log_routing_decision", "lineno": 70, "level": "info", "timestamp": "2"}
```

third:

With more than **"three"** words:
```
how's it going
how's it going
en
how's it going
how's it going
user_query: how's it going
 filtered token: ['going']
0.0
0.0
0.0
0.0
3.0
0.0
0.0
{"category": "CASUAL_TALK", "confidence": 0.99, "model_tier": "Fast", "model_id": "gemini-3.5-flash-lite", "tools": null, "event": "routing decision", "filename": "model_config.py", "func_name": "log_routing_decision", "lineno": 70, "level": "info", "timestamp": "2026-08-24T07:30:06.809418Z"}
```

so what's the conclusion?

That to determine whether NFKC is being ally or enemy to my keyword intent.

suggestion:
Do more research on NFKC and other encoders.


# observation
26/8

I thought of keyword intent confidence

continuing whether nkfc is alies or enemy I think it would be okay to just match the whole think without normalizing it with NFKC

IN simple words if query is "what you doing" should match directly with keyword matching in registry "what you doing".

The compare itself may not left unmeaningful, unnecessary or common words however it should work for keyword intent  because we
are comparing exact words

Note:
Also I commented out the `semantic fallback` in `decision_logic.py` inside short query handle. 

And the reason is if keyword fails waste no time in semantic and fallback to llm.

task:
compare the cost letter latency, token, resource. What is better falling back to semantic or directly fallback to llm.

# obvservation

Error in my thinking:

I said if NFKC is ally or enemy it is neither it has nothing to do with NFKC,

the question come back to stopwords if i m using RIGHT **denominator** to perform confidence score.

I m printing the direct *normalized* word for confidence and obesrve score for a while.

Also thinking of making change in document creation for `semantic` router.

Was it a good call to create document per example.. Or did made a mistake.

task:

I should think more about it before deployment.

think:
does it really help with accuracy if documented individual
does the latency can be imrpoved at all while documented individual
can i find another balance  between latency and accuracy of semantic without using individual documented method.

logs:

```
how's it going
how's it going
how's it going
how's it going
user_query: how's it going
 filtered token: ['how', "'s", 'it', 'going']
0.0
0.0
0.0
0.0
0.75
0.0
0.0
{"category": "CASUAL_TALK", "confidence": 0.75, "model_tier": "Fast", "model_id": "gemini-3.5-flash-lite", "tools": null, "event": "routing decision", "filename": "model_config.py", "func_name": "log_routing_decision", "lineno": 70, "level": "info", "timestamp": "2026-08-26T11:38:03.992308Z"}
```

This is without stopwords the filtered token here does NOT only focus on keywords but it also now compare the stopwords result in 0.75 differenct score.

However i wonder if 's separation by NFKC if they don't will improve the confidence

Trying one without *'s*
how it going
how it going
how it going
how it going
user_query: how it going
 filtered token: ['how', 'it', 'going']
0.0
0.0
0.0
0.0
0.0
0.0
0.0
2026-08-26 17:11:38.755383
...

So we are seeing no match.

This is concerning.

task:
look more into it if not using stopwords is a right call?

29/8

please make sure all the intents are async

# observation

This is insane

Recently i made a changes to my `decision_logic.py` where i opted out the semantic intent in line `74` 

I wanted keyword intent under short query if it were fail fallback directly instead of:

keyword -> semantic -> fallback
i wanted 

keyword -> fallback

and it was strill triggering the `semantic intent` somewhere

which was around line `177` and below 
```
 if keyword_results:
                semantic_results=None
                
            else:
```
so tie log.error **MESSAGE** of semantic timeout was ~
```
  except asyncio.TimeoutError:
                    log.error("keyword intent timed out")
```

and I every time I looked at log i thought it was `keyword` intent timing out.

vedict:

**IT WAS AN ERROR IN LOG MESSAGE IT SUPPOSED TO BE ~ *SEMANTIC INTENT TIMED OUT* *** 

It drives me crazy how low and high i was searching for it, it was right under my nose.

note: *Logging* wrong thing is scary you will be searching for the bug forever and you will never find it.

next focus on ~ how to make keyword intent directly fallback to llm safely.

# observation
9/1

Fallback complete 

Ran into an edge case~

according to my decision logic if length of query != long it triggers keyword first

and if keyword then semantic is none and else trigger semantic

What I actually wanted ~ if query is short keyword if not keyword fallback

if query long semantic if not fallback.

Implementation ~ 
1. write simple match case
2. stick to if elif same thing but different
3. find another way

Applied match/case

however results are pointless because no "pattern" matching, similarly can be done with if/else:

task ~  revert to if/elif/else

Currently taking care of repition in intent intializing intent

# observation

I made a quite a mess today in order to refract the repetition code.

I also find out that i did lot of things messy i wanted it to always return something to user instead of and error message box slightly delayed or wrong answer is better than no answer so i thought 

But I didn't think about internal states failure actual failures needs to be addressed and researched more.

problems in order:

1.  ```   
            # This DOES NOT kill the process when timeout hits
             await asyncio.wait_for(
              loop.run_in_executor(process_pool, semantic_intent, query),
                timeout=5.0
                )
    ```
If semantic_intent takes 3 minutes on CPU, and you timeout after 5 seconds, asyncio raises TimeoutError in your coroutine.

So this is what you call "zombie" because the timeout does NOT work process keeps running in bg until it finishes. Wasted work.

priority : critical issue

2. everything is  return "something"  waterfall method works on signal, if all are happy paths there are no signals.

Part 1 — Make it actually run (~10 min)

1. ctx is never passed to IntentInitializer

     Problem: the function declares ctx as a required keyword argument, but neither call site passes it. Every SHORT/MEDIUM query raises TypeError, which your outer catch-all swallows and converts to fallback. As pasted, your intents never actually execute.
     Fix: you don't need to pass it — item 2 removes the need for ctx in the runner entirely.
     Check: run a short query like "hi" — you should see the keyword path fire, result source="keyword".

Part 2 — Make failure look like failure (~20 min, the important part)

2. IntentInitializer returns the wrong shape on failure

     Problem: on timeout/error it returns asdict(_fallback(ctx)) — a single dict. On success it returns a list of dicts. Then keyword_results[0] on a dict raises KeyError, which gets logged as "catastrophic failure." Every timeout crashes the resolver.
     Fix: replace both failure return statements with return None. Yes — bring None back. Your if keyword_results: guards were already built for it, and None is the correct contract between the runner and the resolver. Also delete the ctx parameter — the runner no longer needs it.
     Check: set timeout=0.001 on the keyword call → a SHORT query should fall cleanly to fallback. No "catastrophic" log, no exception.

3. safe_llm_classifier can never fail

     Problem: every except branch returns a default StrictOutput, which is always truthy. So if llm_result: is always True, and the _fallback(ctx) lines after it in both MEDIUM and LONG are dead code — they can never run.
     Fix: return None in both except branches. Your existing guards take over from there.
     Check: set timeout=0.001 in it → a MEDIUM query with weak semantic results should end at source="fallback", not source="llm".

Part 3 — Small correctness bugs (~15 min)

4. "None" vs "none"

     Problem: the error defaults in safe_llm_classifier use capital-N "None". Everything else uses lowercase. Any downstream tool == "none" check silently fails on the capital version.
     Fix: change to "none". Check: search the file for "None" — should be zero hits.

5. _fallback reads ctx.tools

     Problem: getattr(ctx, "tools", "none") almost certainly grabs a list of tools, putting a list in a string field.
     Fix: hardcode tool="none" in _fallback. A fallback should be a constant you can rely on.
     Check: any fallback result — tool is the string "none", not a list.

6. LONG is handled in two places

     Problem: the else: branch in Decision_logic handles LONG inline, while resolve_intent has a commented-out LONG branch. Two paths for the same tier means the policies will drift apart.
     Fix: delete the inline else branch in Decision_logic entirely. Uncomment the LONG block in resolve_intent, remove its inner try/except (the one that returns f"error: ..." — a string escaping your contract), and let LONG reach resolve_intent with keyword_results=None, semantic_results=None.
     Check: a long query returns source="llm" and every tier now exits through one function.

Part 4 — Hygiene (~20 min, whenever, in any order)

    log.warn → log.warning, log.fatal → log.critical. Both are deprecated, and with structlog they may not exist — meaning the log call itself throws inside your except block and hides the real error.
    except (ValidationError, Exception) → except Exception — the first is already covered by the second.
    asyncio.get_event_loop().run_in_executor(None, func, *args) → asyncio.to_thread(func, *args). Same behavior, modern spelling, not deprecated.
    All the print("... triggered") → log.debug("...", source="keyword") etc.
    0.34 → SEMANTIC_CONFIDENCE_THRESHOLD = 0.34 at the top of the file, used in both places.
    Inconsistency: LONG sends raw query to the LLM, MEDIUM sends normalized. Pick one (probably normalized) and use it everywhere.
    Move IntentInitializer out of Decision_logic to module level. Per-call definition is untestable and won't survive multiprocessing later.
    The non-English gate returns fallback silently — add one log.info there, or you'll never know how much traffic it's eating.

Part 5 — Later, do not touch until 1–4 are done

     The SHORT waterfall (semantic as a lazy partial instead of eager call)
     The process pool for semantic
     A short DECISIONS.md — honestly just paste your own messages from this conversation, they're already better than most engineering blogs

# observation
9/3 

repetition taken care of

keyword working ~ keyword time out (fallback) working
medium query intent triggered working ~ intent time out working 

however getting "catestrophic failure of decision logic"

task ~ investigate what causing the catestrophic failure fix and move one, best guess (because of the result is timed out or something to do with not returning None)

after the continue to fix the failure shape and make failure like failure.

# obervation:

While fixing previous issues.

I asked a question to myself and ai today can `semantic router` latency is fixable?

i do get the yes with few tweaks.

and probably it will be added back to SHORT when semantic will be < 300ms 
also it's laughable at this point but i find out that `tool = "None"` is adversory everwhere because `tools` is already passed to `agent` inside lifespan.

So, no matter the time's i return None for tool its just a log, it doesn't necessarily stop the agent to use any tool.

Currently my tool's are free but as soon as it start costing money this will be a big liability.

Free/internal_tools like get_time, rag_agent (as long as it doesn't cost): can be left bound everywhere, agent disposes at zero risk.

expensive tools (paid apis, anything that cost money to call for a tool): gate  by binding. 
Router endorses the category → the agent variant for that query gets the expensive tool; otherwise it doesn't exist in the agent's world.

The hard guarantee: a budget/rate limit check iinside the expensiee tool itself, it's like a fail safe for a tool itself, no mater what the router or agent decide.


# observation

The 5 part errors and tweaks in `dicision logic` file done.

Moving on to fixing my semantic router for good this time.

when that works re attach it back to waterfall in SHORT.

So let's talk in detail ~
the title is..

## Chase of production system

I remember searching for "production grade ranking system" well after sigmoid it said to be the best practice of using 
a cross encoder instead of bi encoder.

However the cross encoder I chased required a list of [query, example]
basically your query and the data to compare against your query.

cross encoder is amazing but it comes with a cost for me.

the esemble retreiver uses Reciprocal ranking fusion (RRF) it's a ranker it outputs the order of ranked result, not really a number or confidence score you can compare against a threshold.

so the funnel is 500 examples -> 6 examples (by ensemble) -> then back to 75 example (by dict lookup)

```py
results = ensemble_retriever.invoke(query)        # 500 examples → 6 documents
retrieved_categories = set(doc.metadata["category"] for doc in results)  # 6 docs → 3 names

for category in retrieved_categories:
    lookup_examples = pos_lookup[category]        # 3 names → 75 examples (25 each)
    pairs = [[query, ex] for ex in lookup_examples]
    encoder_model.predict(pairs)                  # ← the minutes
```

The cross-encoder never sees the 6 documents retrieval picked. 
It sees 69 examples the retriever implicitly judged less relevant, plus the 6 retrieved ones mixed back in. 
You climb back up the funnel right after descending it.

There's a reason behind it,

Since I changed semantic more than 3 times, logit ranking to sigmoid and now cross encoder re-ranker.

What i wanted is top-3 categories that has most matches the result and then go through all the categories.

Now how do you go through all the categories? two ways previously I used to feed all the example in batch 

but now it does the lookup `lookup_examples = pos_lookup[category] ` and compare query against all example in those **top 3** categories `lets say 25 example each categories (all though I have more) * 3  top categories = 75 total examples`.

Now I have some score for all top 3 categories.

But then a loophole detected that what if a query matches two category very closely how does it decide which one is correct?

so i just compared category1 - category2 and it gave me the gap.

now i have both threshold and gap.

That's what I wanted to achieve and I did but at the cost of `75` cross-encoder calls

But why is this a problem to me?

Because I don't have a GPU fuckkkk.. somebody buy me a 5090. cross ecnoder run terribly slow in CPU (ofc i didn't knew that before using reranker).

Deploying methods to solve this fucked up starting from tomorrow.



# observation

Traceback (most recent call last):
  File "d:\Documents\Project_x\x v5\intent_router.py", line 390, in <module>
    test2 = semantic_intent("heyllo")
            ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\Documents\Project_x\x v5\intent_router.py", line 384, in semantic_intent
    return _winner(best_cat, best_score)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: _winner() takes 1 positional argument but 2 were given
(project_venv) PS D:\Documents> 
last error before packing up


# observation

9/19

Semantic Intent up running yet to check the end-to-end working

I will walk you what changed what were the problems I faced but for now lets just say banzai

After 100s of search everyday and a bit of ai help it's working with better latency then before and performance as well.


9/30
# lot happened 














































































many things I can't figure out some things clicked now

i want to take this project to end as soon as possible i extended it already so fixing the semantic is hopefully my last big headache to make it minimally working.

it is working since we ditched the whole bgm re ranker and using light weight ranker we are relying on it we also ditched the result of ensemble retriever

It is working but still need few things twigged

what's better is the latency not satisfied but better than before

right now i m thinking of using back the ensemble retreiver result back somehow.

second i don't want to see error in my stdout for empty results of semantic

#  Continue

start writing very basic one page UI for the project

# conclusion

today i have reached the conclusion of semantic decision

Semantic and the query intent is done for now, i have tried different models of embeddings, rankers to compare latency, results, accuracy, the router's job is cheap and mostly right and the mariginal house was worth more on the rest of the system.

In future however i could try many multiple things such as logistic training an embedding specifically to catch the intent, using a high accuracy re ranker, more example/ documents for embedding etc.

However due to latency limitation i m going to stop here, i m not nearly satisfied with the accuracy and latency but it works

i will in future try to improve it further.

# next

eval data:

a simple data to check the threshold of semantic, keyword

total output token usage, output and generation time.

tool token usage time, tool response/ help generation time

all in a database

eval to stress the check the model responses, guard rails



# 1/11

while testing the model i ran into depreciation warning
DeprecationWarning: `langchain-community` is being sunset and is no longer actively maintained. See <https://github.com/langchain-ai/langchain-community/issues/674> for details and migration guidance toward standalone integration packages.
  from langchain_community.retrievers import BM25Retriever

# busy satisfying type checker

Modern LLM frameworks (like Anthropic, LangChain, or custom Pydantic projects) do not accept plain strings (str) for API keys anymore. They require a SecretStr object.
• Security Reason: SecretStr prevents sensitive keys from accidentally leaking into terminal prints, application logs, or error traces.
• Type-Checker Conflict: os.getenv("KEY") returns str | None. Passing this directly to something expecting SecretStr | None triggers strict static typing errors (red squiggly lines).

• Rule 1: Never pass os.getenv() directly into a function parameter explicitly typed as SecretStr.
• Rule 2: If doing it outside a Pydantic model, manually wrap it conditional on its existence:
SecretStr(key) if key is not None else None
• Rule 3: Inside a standard Pydantic model, pass the raw string straight to the instantiation block (Model(key=raw_str)). Pydantic takes care of the internal type conversion automatically.

Updated IN: model_config os.getenv to pydantic class with Basesettings which seems to automatically find the key in env and i did
           `case_sesnsitive =  False` because the variable name are in Uppercase in ENV.

           the secretstr is actually good stuff it just print `(***********)` when you print or access key explciitly.

`SECRETSTR` remember is the security star

The debugger has green lit all type checker green lit moving to new file


# 3/11 

CHROMA DB I was fixing the path and I was thinking about pinecone I just wanted to try it once

and since CHROMA DB is built for local development and prototyping i think its good time to transit to **Pinecone**

Well CHROMA was good literally zero configuration just install chromadb 

since Pinecone is **CLOUD NATIVE** Vector DB

i may have to setup API keys

and just MAYBEEE pinecone could be overkill for what I am doing but that's fine we are doing this for the sake of "trying" it out
for testing.

IDK much about Pinecone but hopefully i won't see any performance and latency overhead still we will see since API is involved i gotta check out how it works but that will be after deployment

or IF NOT pgvector since i m already using postgres SQL `pgvector` can be unified for now i m transitioning to that then i will later do Pinecone

~ marked for after deployment
#######################################################################################

# 4/11 RAG tool: MCP to local tool

I moved the RAG agent from an MCP stdio server to a local LangChain tool inside the FastAPI app.

The RAG agent was only used by this app. With stdio MCP, the main agent had to cross a process boundary to call it, and the adapter starts a server process for tool calls. That made it harder to keep and reuse the RAG agent between requests.

Now FastAPI creates the RAG tool during lifespan startup and gives it to the main agents. So the RAG agent stays in the app process and can be reused. The document retriever still loads only when a document search actually happens.

This doesn't mean MCP is bad. MCP would make more sense if I wanted the RAG service to run separately, let other apps use it, or build it in another language. For now it is an internal tool for one app, so the local tool is a simpler fit.

Don't claim I measured a latency improvement because I haven't benchmarked it. The actual reasons are less process-boundary complexity and reusing the agent in the same process.

#######################################################################################
