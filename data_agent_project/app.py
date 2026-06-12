import os
from pathlib import Path

import streamlit as st
import pandas as pd
import sqlite3

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI

DB_PATH = Path(__file__).parent / "db" / "careers.db"

st.set_page_config(page_title="求职数据分析智能体", page_icon="💼", layout="wide")

st.title("💼 求职数据分析智能体")
st.markdown("基于 LangChain + SQLite 的求职市场自然语言分析系统")


@st.cache_resource
def load_llm():
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "local-model"),
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:8080/v1"),
        api_key="not-needed",
        temperature=0,
        max_tokens=2048,
    )


@st.cache_resource
def load_database():
    if not DB_PATH.exists():
        st.error(f"数据库不存在: {DB_PATH}")
        st.info("请先运行: python scripts/generate_job_data.py")
        st.stop()
    return SQLDatabase.from_uri(f"sqlite:///{DB_PATH.as_posix()}")


@st.cache_resource
def load_agent(_llm, _db):
    return create_sql_agent(llm=_llm, db=_db, agent_type="openai-tools", verbose=True)


def get_table_info():
    info = {}
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            info[table] = count
    return info


def get_table_dataframe(table_name, limit=100):
    with sqlite3.connect(str(DB_PATH)) as conn:
        return pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {limit}", conn)


def query_with_agent(agent, question):
    result = agent.invoke({"input": question})
    return result.get("output", "无法生成回答")


SAMPLE_QUESTIONS = {
    "市场热度分析": [
        "哪些技能在求职市场上最热门？",
        "各技能的趋势评分如何？",
        "AI相关岗位占比多少？",
    ],
    "地域分布分析": [
        "哪些城市的岗位最多？",
        "北京和上海的岗位有什么差异？",
        "广东有哪些类型的岗位？",
    ],
    "薪资分析": [
        "薪资最高的10个岗位是什么？",
        "不同经验要求的薪资差异如何？",
        "AI岗位和普通开发岗位薪资对比？",
    ],
    "公司分析": [
        "哪些公司招聘岗位最多？",
        "B轮公司的薪资范围是多少？",
        "大厂和创业公司的岗位差异？",
    ],
    "技能匹配": [
        "Python岗位需要哪些技能？",
        "RAG相关的岗位有哪些？",
        "应届生适合投递哪些岗位？",
    ],
}


def main():
    llm = load_llm()
    db = load_database()
    agent = load_agent(llm, db)

    with st.sidebar:
        st.header("📊 数据库概览")
        table_info = get_table_info()
        for table, count in table_info.items():
            st.metric(table, f"{count} 条")

        st.divider()
        st.header("⚙️ 配置")
        base_url = st.text_input("LLM API URL", value=os.getenv("LLM_BASE_URL", "http://localhost:8080/v1"))
        model_name = st.text_input("模型名称", value=os.getenv("LLM_MODEL", "local-model"))
        if base_url != os.getenv("LLM_BASE_URL", "http://localhost:8080/v1") or \
           model_name != os.getenv("LLM_MODEL", "local-model"):
            os.environ["LLM_BASE_URL"] = base_url
            os.environ["LLM_MODEL"] = model_name
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["💬 智能查询", "📋 数据浏览", "📈 预设分析"])

    with tab1:
        st.subheader("自然语言查询")
        question = st.text_input("输入您的问题：", placeholder="例如：哪些技能在求职市场上最热门？")
        if st.button("🔍 查询", type="primary") and question:
            with st.spinner("正在分析..."):
                answer = query_with_agent(agent, question)
            st.success("查询完成！")
            st.markdown("### 回答")
            st.markdown(answer)

    with tab2:
        st.subheader("数据浏览")
        tables = list(table_info.keys())
        selected_table = st.selectbox("选择表", tables)
        if selected_table:
            df = get_table_dataframe(selected_table, limit=100)
            st.dataframe(df, use_container_width=True)
            st.markdown(f"**表共 {table_info[selected_table]} 条记录，显示前 100 条**")

    with tab3:
        st.subheader("预设分析场景")
        for category, questions in SAMPLE_QUESTIONS.items():
            with st.expander(f"📊 {category}", expanded=False):
                for q in questions:
                    if st.button(q, key=q):
                        with st.spinner("正在查询..."):
                            answer = query_with_agent(agent, q)
                        st.markdown(f"**问题：** {q}")
                        st.markdown(f"**回答：** {answer}")


if __name__ == "__main__":
    main()
