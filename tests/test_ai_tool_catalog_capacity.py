from opencoach.ai.schemas import AIChatRequest, AIMessage, AIToolDefinition


def test_ai_chat_request_accepts_expanded_tool_catalog():
    tools = [
        AIToolDefinition(
            name=f"tool_{index}",
            description=f"Test tool {index}",
            parameters={"type": "object", "properties": {}},
        )
        for index in range(11)
    ]

    request = AIChatRequest(
        messages=[AIMessage(role="user", content="Analyse mon entraînement.")],
        tools=tools,
    )

    assert len(request.tools) == 11
