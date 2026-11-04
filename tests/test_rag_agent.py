import asyncio

from langchain_core.messages import AIMessage

import tools.rag_mcp as rag_agent_module


def test_create_rag_tool_reuses_agent(monkeypatch):
    class FakeAgent:
        async def ainvoke(self, payload):
            assert payload["messages"][0].content == "document question"
            return {"messages": [AIMessage(content="document answer")]}

    created_agents = []
    monkeypatch.setattr(rag_agent_module, "model_endpoint", lambda tier: object())
    monkeypatch.setattr(
        rag_agent_module,
        "create_agent",
        lambda **kwargs: created_agents.append(FakeAgent()) or created_agents[-1],
    )

    rag_tool = rag_agent_module.create_rag_tool()

    assert rag_tool.name == "rag"
    assert asyncio.run(rag_tool.ainvoke({"query": "document question"})) == "document answer"
    assert asyncio.run(rag_tool.ainvoke({"query": "document question"})) == "document answer"
    assert len(created_agents) == 1
