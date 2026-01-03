import os
from typing import List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

_llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0.7,
    max_tokens=180,
)

def _map_history_to_openai(history_docs: List[Dict]) -> List[Dict]:
    # Convert Mongo role -> OpenAI role
    out = []
    for d in history_docs:
        if d["role"] == "salesperson":
            out.append({"role": "user", "content": d["text"]})
        else:
            out.append({"role": "assistant", "content": d["text"]})
    return out


async def generate_customer_reply(system_prompt: str, few_shot: List[Dict], history_docs: List[Dict], salesperson_message: str) -> str:
    history_msgs = _map_history_to_openai(history_docs)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            *[(m["role"], m["content"]) for m in few_shot],
            MessagesPlaceholder("history"),
            ("user", "{salesperson_message}"),
        ]
    )

    chain = prompt | _llm
    resp = await chain.ainvoke(
        {"history": history_msgs, "salesperson_message": salesperson_message}
    )
    return resp.content.strip()
