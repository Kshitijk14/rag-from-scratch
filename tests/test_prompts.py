from utils.prompts import REWRITE_PROMPT, ROUTER_PROMPT, SQL_PROMPT


def test_prompts_have_placeholders():
    prompts = [
        ("REWRITE", REWRITE_PROMPT, {"schema_context": "abc", "question": "q?"}),
        ("ROUTER", ROUTER_PROMPT, {"table_list": "t1", "rewritten": "x"}),
        ("SQL", SQL_PROMPT, {
            "schema_context": "abc",
            "rewritten": "x",
            "tables": "T1,T2",
            "join_hints": "id=ID",
        }),
    ]

    for name, p, kwargs in prompts:
        rendered = p.format_prompt(**kwargs)
        messages = rendered.to_messages()
        assert len(messages) > 0, f"{name}: no messages"

        all_text = "\n".join(m.content for m in messages if hasattr(m, "content"))
        for v in kwargs.values():
            assert str(v) in all_text, f"{name}: missing {v}"
