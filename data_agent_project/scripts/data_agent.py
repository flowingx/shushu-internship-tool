import os
import sys
from pathlib import Path

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI

DB_PATH = Path(__file__).parent.parent / "db" / "careers.db"

DEFAULT_LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8080/v1")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "local-model")

SAMPLE_QUESTIONS = [
    "哪些技能在求职市场上最热门？",
    "北京有哪些AI相关的岗位？",
    "薪资最高的10个岗位是什么？",
    "Python岗位在哪些城市需求最多？",
    "B轮公司的岗位薪资范围是多少？",
    "RAG相关的技能趋势如何？",
    "哪些项目模板适合用来准备面试？",
    "应届生可以投递哪些岗位？",
]


def get_llm(base_url=None, model=None):
    base_url = base_url or DEFAULT_LLM_BASE_URL
    model = model or DEFAULT_LLM_MODEL
    print(f"Connecting to LLM at: {base_url}")
    return ChatOpenAI(model=model, base_url=base_url, api_key="not-needed", temperature=0, max_tokens=2048)


def get_database():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Please run: python scripts/generate_job_data.py")
        sys.exit(1)
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH.as_posix()}")
    print(f"Connected to: {DB_PATH}")
    print(f"Tables: {db.get_usable_table_names()}")
    return db


def create_agent(llm, db):
    return create_sql_agent(llm=llm, db=db, agent_type="openai-tools", verbose=True)


def query_agent(agent, question):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print("=" * 60)
    result = agent.invoke({"input": question})
    print(f"\nAnswer:\n{result.get('output', 'No output')}")
    print("=" * 60)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Job Market Data Analysis Agent")
    parser.add_argument("--question", "-q", type=str, help="Natural language question")
    parser.add_argument("--base-url", type=str, default=None)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument("--samples", "-s", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("Job Market Data Analysis Agent")
    print("=" * 60)

    llm = get_llm(args.base_url, args.model)
    db = get_database()
    agent = create_agent(llm, db)

    if args.question:
        query_agent(agent, args.question)
    elif args.samples:
        for q in SAMPLE_QUESTIONS:
            query_agent(agent, q)
    elif args.interactive:
        print("\nInteractive mode. Type 'quit' to exit.")
        while True:
            q = input("\nYour question: ").strip()
            if q.lower() in ("quit", "exit", "q"):
                break
            if q:
                query_agent(agent, q)
    else:
        for q in SAMPLE_QUESTIONS:
            query_agent(agent, q)


if __name__ == "__main__":
    main()
