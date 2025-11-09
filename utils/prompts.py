from textwrap import dedent

from langchain_core.prompts import ChatPromptTemplate


REWRITE_PROMPT = ChatPromptTemplate.from_template(dedent(
    """
        You are a database assistant. Given a user's vague question and the available table schema summaries,
            1) identify the main analytical intent,
            2) produce 1-3 precise sub-questions that would retrieve the necessary fields,
            3) rewrite the question as a schema-aware, technically specific NLQ.

        SCHEMAS/SUMMARIES:\n{schema_context}

        USER QUESTION: {question}

        Return JSON with keys: intent, sub_questions, rewritten.
    """
))


ROUTER_PROMPT = ChatPromptTemplate.from_template(dedent(
    """
        You are a table router. Given the rewritten NLQ and the available tables,
        choose the minimal set of tables needed and list the join keys if joins are necessary.

        TABLES:\n{table_list}

        NLQ: {rewritten}

        Return JSON with keys: tables (list of table names), join_hints (list of strings).
    """
))


SQL_PROMPT = ChatPromptTemplate.from_template(dedent(
    """
        You are an expert Oracle SQL generator. Use ONLY the provided table DDL fragments and summaries.
            - Output a single Oracle SELECT statement, no comments.
            - Use explicit table aliases.
            - Respect data types and available columns.
            - Enforce ROWNUM filters only if asked; otherwise do not add limits.

        DIALECT: Oracle

        DDL/SUMMARY CONTEXT:\n{schema_context}

        NLQ: {rewritten}
        TARGET TABLES: {tables}
        JOIN HINTS: {join_hints}
    """
))


FEW_SHOT_EXAMPLES = [
    {
        "nlq": "total paid chargebacks in 2024, statuses 5 and 6",
        "sql": (
            "SELECT SUM(C.CHARGE_AMT) AS total_paid_chargebacks\n"
            "FROM VNC_OWNER.CHGBK C\n"
            "WHERE C.BATCH_ID != 0\n"
                "AND C.STATUS_ID IN (5,6)\n"
                "AND C.CREATE_DT >= TO_DATE('2024-01-01','YYYY-MM-DD')\n"
                "AND C.CREATE_DT < TO_DATE('2025-01-01','YYYY-MM-DD')"
        ),
    },
    {
        "nlq": "total paid accessorial chargebacks in 2024, statuses 5 and 6",
        "sql": (
            "SELECT SUM(C.CHARGE_AMT) AS total_paid_chargebacks\n"
            "FROM VNC_OWNER.CHGBK C\n"
            "INNER JOIN VNC_OWNER.ACCESSORIAL A ON A.GLOBAL_ID = C.GLOBAL_ID\n"
            "WHERE C.BATCH_ID != 0\n"
                "AND C.STATUS_ID IN (5, 6)\n"
                "AND C.CREATE_DT >= TO_DATE('2024-01-01', 'YYYY-MM-DD')\n"
                "AND C.CREATE_DT < TO_DATE('2025-01-01', 'YYYY-MM-DD')\n"
        ),
    },
]