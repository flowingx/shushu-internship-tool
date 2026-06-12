from __future__ import annotations

import csv
import re
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any


JOB_COLUMNS = [
    "category",
    "sub_category",
    "job_title",
    "province",
    "job_location",
    "job_company",
    "job_industry",
    "job_finance",
    "job_scale",
    "job_welfare",
    "job_salary_range",
    "job_experience",
    "job_education",
    "job_skills",
    "create_time",
]


SAMPLE_JOBS: list[dict[str, Any]] = [
    {
        "category": "互联网/AI",
        "sub_category": "AI应用",
        "job_title": "AI应用工程师",
        "province": "广东",
        "job_location": "深圳",
        "job_company": "星河智能科技",
        "job_industry": "人工智能",
        "job_finance": "B轮",
        "job_scale": "100-499人",
        "job_welfare": "五险一金、弹性工作、项目奖金",
        "job_salary_range": "18-30K",
        "job_experience": "1-3年",
        "job_education": "本科",
        "job_skills": "Python, FastAPI, LangChain, RAG, 向量数据库, Docker, SQL",
        "create_time": "2026-06",
    },
    {
        "category": "互联网/AI",
        "sub_category": "大模型",
        "job_title": "大模型应用开发工程师",
        "province": "上海",
        "job_location": "上海",
        "job_company": "澜舟数据",
        "job_industry": "企业服务",
        "job_finance": "A轮",
        "job_scale": "50-99人",
        "job_welfare": "年终奖、餐补、技术分享",
        "job_salary_range": "20-35K",
        "job_experience": "1-3年",
        "job_education": "本科",
        "job_skills": "Python, LLM API, Prompt Engineering, RAG, Milvus, Redis, Git",
        "create_time": "2026-06",
    },
    {
        "category": "开发/后端",
        "sub_category": "Python",
        "job_title": "Python后端开发工程师",
        "province": "北京",
        "job_location": "北京",
        "job_company": "云杉科技",
        "job_industry": "SaaS",
        "job_finance": "C轮",
        "job_scale": "500-999人",
        "job_welfare": "补充医疗、带薪年假、股票期权",
        "job_salary_range": "16-28K",
        "job_experience": "1-3年",
        "job_education": "本科",
        "job_skills": "Python, FastAPI, SQLAlchemy, MySQL, Redis, Docker, Linux",
        "create_time": "2026-06",
    },
    {
        "category": "数据",
        "sub_category": "数据分析",
        "job_title": "数据分析师",
        "province": "浙江",
        "job_location": "杭州",
        "job_company": "青禾电商",
        "job_industry": "电商",
        "job_finance": "不需要融资",
        "job_scale": "1000-9999人",
        "job_welfare": "双休、餐补、年度体检",
        "job_salary_range": "12-20K",
        "job_experience": "1-3年",
        "job_education": "本科",
        "job_skills": "SQL, Python, pandas, 可视化, 业务分析, A/B测试",
        "create_time": "2026-06",
    },
    {
        "category": "互联网/AI",
        "sub_category": "Agent",
        "job_title": "AI Agent开发实习生",
        "province": "北京",
        "job_location": "北京",
        "job_company": "北辰智算",
        "job_industry": "人工智能",
        "job_finance": "天使轮",
        "job_scale": "20-49人",
        "job_welfare": "远程办公、导师制、转正机会",
        "job_salary_range": "250-400元/天",
        "job_experience": "在校/应届",
        "job_education": "本科",
        "job_skills": "Python, LangChain, LangGraph, RAG, 工具调用, SQL, Git",
        "create_time": "2026-06",
    },
    {
        "category": "互联网/AI",
        "sub_category": "工程化",
        "job_title": "LLM平台工程师",
        "province": "江苏",
        "job_location": "南京",
        "job_company": "数桥云",
        "job_industry": "云计算",
        "job_finance": "上市公司",
        "job_scale": "1000-9999人",
        "job_welfare": "五险一金、补充公积金、带薪年假",
        "job_salary_range": "22-40K",
        "job_experience": "3-5年",
        "job_education": "本科",
        "job_skills": "Python, Kubernetes, Docker, LLM API, 监控, 评测, FastAPI",
        "create_time": "2026-06",
    },
]


SKILL_ALIASES = {
    "Python": ["python", "py", "pandas", "numpy"],
    "SQL": ["sql", "mysql", "postgresql", "sqlite", "数据库"],
    "FastAPI": ["fastapi", "flask", "后端接口", "api"],
    "LangChain": ["langchain"],
    "LangGraph": ["langgraph"],
    "RAG": ["rag", "检索增强", "知识库", "知识库问答"],
    "LLM API": ["llm", "大模型", "openai", "通义", "智谱", "moonshot", "deepseek", "模型api"],
    "Prompt Engineering": ["prompt", "提示词", "提示工程"],
    "Vector DB": ["向量数据库", "milvus", "faiss", "chromadb", "pgvector", "vector"],
    "Docker": ["docker", "容器"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Redis": ["redis"],
    "Git": ["git", "github", "gitlab"],
    "Evaluation": ["评测", "eval", "测试集", "benchmark"],
    "Monitoring": ["监控", "日志", "observability", "可观测"],
    "Visualization": ["可视化", "plotly", "streamlit", "echarts", "tableau", "power bi"],
}


PROJECT_TEMPLATES = [
    {
        "name": "企业知识库 RAG 问答系统",
        "level": "核心项目",
        "skills": ["Python", "RAG", "LangChain", "Vector DB", "LLM API", "FastAPI"],
        "deliverable": "支持上传文档、向量检索、带引用回答、Web API",
        "why": "覆盖 AI 应用岗位最常见的知识库和检索增强需求。",
    },
    {
        "name": "数据库 SQL Agent 分析助手",
        "level": "课程项目",
        "skills": ["Python", "SQL", "LangChain", "LLM API", "Visualization"],
        "deliverable": "自然语言提问、生成只读 SQL、结果表格、图表解释",
        "why": "和数据库课程强相关，也能展示 agent 不是单纯聊天。",
    },
    {
        "name": "多工具求职 Agent",
        "level": "进阶项目",
        "skills": ["Python", "LangGraph", "LLM API", "Git", "Evaluation"],
        "deliverable": "岗位解析、技能匹配、项目推荐、面试题生成",
        "why": "复用原仓库能力，展示工具调用、状态流转和推荐依据。",
    },
    {
        "name": "LLM 应用评测与日志平台",
        "level": "工程化项目",
        "skills": ["Python", "Evaluation", "Monitoring", "SQL", "Visualization"],
        "deliverable": "保存 prompt、回答、评分、失败案例和趋势图",
        "why": "补齐 AI 应用工程中经常被忽视的评测和可观测能力。",
    },
    {
        "name": "AI 应用部署模板",
        "level": "工程化项目",
        "skills": ["FastAPI", "Docker", "Redis", "Git", "Monitoring"],
        "deliverable": "FastAPI 服务、Dockerfile、缓存、日志和健康检查",
        "why": "把 demo 变成可部署服务，面试时更像真实工程。",
    },
]


LEARNING_RESOURCES = [
    {"skill": "RAG", "title": "RAG 原理到企业知识库实战", "type": "项目文档", "focus": "检索、重排、引用、幻觉控制"},
    {"skill": "LangChain", "title": "LangChain SQL Agent 与 Tool Calling", "type": "框架练习", "focus": "工具调用、SQLDatabase、只读查询约束"},
    {"skill": "FastAPI", "title": "FastAPI 服务化最小模板", "type": "工程模板", "focus": "接口、参数校验、日志、健康检查"},
    {"skill": "Docker", "title": "AI 应用 Docker 部署清单", "type": "部署清单", "focus": "镜像、环境变量、启动脚本、端口"},
    {"skill": "Evaluation", "title": "LLM 应用评测用例库", "type": "面试准备", "focus": "准确率、失败案例、回归测试、日志分析"},
    {"skill": "SQL", "title": "岗位市场分析 SQL 题", "type": "课程练习", "focus": "分组统计、关联查询、共现分析、视图"},
]


SKILL_TRENDS = [
    {"skill": "RAG", "trend_score": 95, "signal": "上升", "source": "Job-SDF副数据接口"},
    {"skill": "LLM API", "trend_score": 91, "signal": "上升", "source": "Job-SDF副数据接口"},
    {"skill": "Vector DB", "trend_score": 88, "signal": "上升", "source": "Job-SDF副数据接口"},
    {"skill": "LangChain", "trend_score": 84, "signal": "上升", "source": "Job-SDF副数据接口"},
    {"skill": "Evaluation", "trend_score": 79, "signal": "上升", "source": "Job-SDF副数据接口"},
    {"skill": "Docker", "trend_score": 66, "signal": "稳定", "source": "Job-SDF副数据接口"},
    {"skill": "SQL", "trend_score": 62, "signal": "稳定", "source": "Job-SDF副数据接口"},
    {"skill": "Redis", "trend_score": 56, "signal": "稳定", "source": "Job-SDF副数据接口"},
]


SCHEMA_SQL = """
create table raw_jobs (
  job_id integer primary key,
  category text,
  sub_category text,
  job_title text,
  province text,
  job_location text,
  job_company text,
  job_industry text,
  job_finance text,
  job_scale text,
  job_welfare text,
  job_salary_range text,
  job_experience text,
  job_education text,
  job_skills text,
  create_time text,
  salary_floor_k real
);

create table job_skill_map (
  job_id integer not null,
  skill text not null,
  foreign key(job_id) references raw_jobs(job_id)
);

create table project_templates (
  project_id integer primary key,
  name text not null,
  level text,
  deliverable text,
  why text
);

create table project_skill_map (
  project_id integer not null,
  skill text not null,
  foreign key(project_id) references project_templates(project_id)
);

create table learning_resources (
  resource_id integer primary key,
  skill text not null,
  title text not null,
  type text,
  focus text
);

create table skill_trends (
  skill text primary key,
  trend_score integer not null,
  signal text,
  source text
);

create table app_metadata (
  key text primary key,
  value text
);
"""


def normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def split_raw_skills(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,，、/;；|｜\s]+", normalize_text(value)) if part.strip()]


def extract_skills(text: str) -> list[str]:
    lower_text = normalize_text(text).lower()
    found: list[str] = []
    for skill, aliases in SKILL_ALIASES.items():
        if any(alias.lower() in lower_text for alias in aliases):
            found.append(skill)
    return sorted(set(found))


def canonical_skill(skill: str) -> str | None:
    clean = normalize_text(skill)
    if not clean or len(clean) <= 1:
        return None
    lower = clean.lower()
    for canonical, aliases in SKILL_ALIASES.items():
        if lower == canonical.lower() or lower in [alias.lower() for alias in aliases]:
            return canonical
    return clean


def salary_floor(value: str) -> float | None:
    text = normalize_text(value).lower()
    month = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*k", text)
    if month:
        return float(month.group(1))
    day = re.search(r"(\d+)\s*-\s*(\d+)\s*元/天", text)
    if day:
        return round(float(day.group(1)) * 21 / 1000, 1)
    return None


def load_jobs(raw_csv: str | Path | None = None) -> list[dict[str, Any]]:
    if raw_csv and Path(raw_csv).exists():
        with Path(raw_csv).open("r", encoding="utf-8-sig", newline="") as handle:
            rows = []
            for item in csv.DictReader(handle):
                rows.append({column: normalize_text(item.get(column, "")) for column in JOB_COLUMNS})
            return rows
    return [dict(row) for row in SAMPLE_JOBS]


def source_signature(raw_csv: str | Path | None = None) -> str:
    if raw_csv and Path(raw_csv).exists():
        path = Path(raw_csv)
        stat = path.stat()
        return f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}"
    return "sample-jobs-v2"


def build_database(db_path: str | Path, raw_csv: str | Path | None = None) -> Path:
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    jobs = load_jobs(raw_csv)

    temp_path = Path(tempfile.gettempdir()) / f"{db.stem}.building{db.suffix}"
    if temp_path.exists():
        temp_path.unlink()

    with closing(sqlite3.connect(temp_path, timeout=10)) as conn:
        conn.executescript(SCHEMA_SQL)
        for job_id, row in enumerate(jobs, 1):
            payload = {column: row.get(column, "") for column in JOB_COLUMNS}
            conn.execute(
                """
                insert into raw_jobs (
                  job_id, category, sub_category, job_title, province, job_location,
                  job_company, job_industry, job_finance, job_scale, job_welfare,
                  job_salary_range, job_experience, job_education, job_skills,
                  create_time, salary_floor_k
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    payload["category"],
                    payload["sub_category"],
                    payload["job_title"],
                    payload["province"],
                    payload["job_location"],
                    payload["job_company"],
                    payload["job_industry"],
                    payload["job_finance"],
                    payload["job_scale"],
                    payload["job_welfare"],
                    payload["job_salary_range"],
                    payload["job_experience"],
                    payload["job_education"],
                    payload["job_skills"],
                    payload["create_time"],
                    salary_floor(payload["job_salary_range"]),
                ),
            )
            skill_blob = " ".join([payload["job_title"], payload["job_skills"], payload["job_industry"]])
            skills = set(extract_skills(skill_blob))
            skills.update(split_raw_skills(payload["job_skills"]))
            for raw_skill in sorted(skills):
                if skill := canonical_skill(raw_skill):
                    conn.execute("insert into job_skill_map(job_id, skill) values (?, ?)", (job_id, skill))

        for project_id, project in enumerate(PROJECT_TEMPLATES, 1):
            conn.execute(
                "insert into project_templates(project_id, name, level, deliverable, why) values (?, ?, ?, ?, ?)",
                (project_id, project["name"], project["level"], project["deliverable"], project["why"]),
            )
            for skill in project["skills"]:
                conn.execute("insert into project_skill_map(project_id, skill) values (?, ?)", (project_id, skill))

        for resource_id, resource in enumerate(LEARNING_RESOURCES, 1):
            conn.execute(
                "insert into learning_resources(resource_id, skill, title, type, focus) values (?, ?, ?, ?, ?)",
                (resource_id, resource["skill"], resource["title"], resource["type"], resource["focus"]),
            )

        for trend in SKILL_TRENDS:
            conn.execute(
                "insert into skill_trends(skill, trend_score, signal, source) values (?, ?, ?, ?)",
                (trend["skill"], trend["trend_score"], trend["signal"], trend["source"]),
            )

        conn.executescript(
            """
            create index idx_raw_jobs_title on raw_jobs(job_title);
            create index idx_raw_jobs_location on raw_jobs(job_location);
            create index idx_job_skill_skill on job_skill_map(skill);
            create index idx_job_skill_job on job_skill_map(job_id);
            create index idx_project_skill_skill on project_skill_map(skill);
            create index idx_resource_skill on learning_resources(skill);
            """
        )
        conn.execute(
            "insert into app_metadata(key, value) values (?, ?)",
            ("source_signature", source_signature(raw_csv)),
        )
        conn.commit()

    shutil.copy2(temp_path, db)
    temp_path.unlink()
    return db


def database_is_current(db_path: str | Path, raw_csv: str | Path | None = None) -> bool:
    db = Path(db_path)
    if not db.exists():
        return False
    try:
        with closing(sqlite3.connect(db, timeout=5)) as conn:
            row = conn.execute(
                "select value from app_metadata where key = 'source_signature'"
            ).fetchone()
            return bool(row and row[0] == source_signature(raw_csv))
    except sqlite3.Error:
        return False


def ensure_database(db_path: str | Path, raw_csv: str | Path | None = None) -> Path:
    if not database_is_current(db_path, raw_csv):
        return build_database(db_path, raw_csv)
    return Path(db_path)


def query_rows(db_path: str | Path, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(db_path, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def market_frequency(db_path: str | Path, limit: int = 15) -> list[dict[str, Any]]:
    return query_rows(
        db_path,
        """
        select skill, count(distinct job_id) as job_count
        from job_skill_map
        group by skill
        order by job_count desc, skill asc
        limit ?
        """,
        (limit,),
    )


def skill_trends(db_path: str | Path) -> list[dict[str, Any]]:
    return query_rows(
        db_path,
        "select skill, trend_score, signal, source from skill_trends order by trend_score desc",
    )


def similar_jobs(db_path: str | Path, target_skills: list[str], keyword: str = "") -> list[dict[str, Any]]:
    if target_skills:
        placeholders = ",".join(["?"] * len(target_skills))
        return query_rows(
            db_path,
            f"""
            select r.job_id, r.job_title, r.job_company, r.job_location,
                   r.job_salary_range, count(distinct m.skill) as matched_skills,
                   group_concat(distinct m.skill) as skill_hits
            from raw_jobs r
            join job_skill_map m on r.job_id = m.job_id
            where m.skill in ({placeholders})
            group by r.job_id
            order by matched_skills desc, r.salary_floor_k desc
            limit 10
            """,
            tuple(target_skills),
        )
    like = f"%{keyword}%"
    return query_rows(
        db_path,
        """
        select job_id, job_title, job_company, job_location, job_salary_range,
               0 as matched_skills, job_skills as skill_hits
        from raw_jobs
        where job_title like ? or job_skills like ? or sub_category like ?
        limit 10
        """,
        (like, like, like),
    )


def score_projects(
    target_skills: list[str],
    frequency_rows: list[dict[str, Any]],
    trend_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    frequency = {row["skill"]: int(row["job_count"]) for row in frequency_rows}
    trend = {row["skill"]: int(row["trend_score"]) for row in trend_rows}
    target = set(target_skills)
    scored = []
    for project in PROJECT_TEMPLATES:
        skills = set(project["skills"])
        covered = sorted(skills & target)
        missing = sorted(target - skills)
        market_bonus = sum(frequency.get(skill, 0) for skill in skills)
        trend_bonus = round(sum(trend.get(skill, 0) for skill in skills) / 25)
        scored.append(
            {
                "项目": project["name"],
                "类型": project["level"],
                "匹配分": len(covered) * 12 + market_bonus + trend_bonus,
                "覆盖技能": "、".join(covered) if covered else "待补充目标技能",
                "还需补": "、".join(missing[:6]) if missing else "无",
                "趋势加权": trend_bonus,
                "交付物": project["deliverable"],
                "推荐理由": project["why"],
            }
        )
    return sorted(scored, key=lambda row: (-int(row["匹配分"]), str(row["项目"])))


def recommend_resources(db_path: str | Path, skills: list[str]) -> list[dict[str, Any]]:
    if not skills:
        return []
    placeholders = ",".join(["?"] * len(skills))
    return query_rows(
        db_path,
        f"""
        select skill, title, type, focus
        from learning_resources
        where skill in ({placeholders})
        order by skill, type
        """,
        tuple(skills),
    )


def project_coverage_matrix(project_rows: list[dict[str, Any]], skills: list[str]) -> list[dict[str, Any]]:
    template_skills = {project["name"]: set(project["skills"]) for project in PROJECT_TEMPLATES}
    matrix = []
    for project in project_rows[:5]:
        row: dict[str, Any] = {"项目": project["项目"]}
        for skill in skills:
            row[skill] = 1 if skill in template_skills.get(project["项目"], set()) else 0
        matrix.append(row)
    return matrix


def analyze_target(db_path: str | Path, jd_text: str, keyword: str, known_text: str = "") -> dict[str, Any]:
    target_skills = extract_skills(" ".join([jd_text, keyword]))
    known_skills = extract_skills(known_text)
    gap_skills = sorted(set(target_skills) - set(known_skills))
    planning_skills = gap_skills or target_skills
    frequency = market_frequency(db_path)
    trends = skill_trends(db_path)
    projects = score_projects(planning_skills, frequency, trends)
    return {
        "target_skills": target_skills,
        "known_skills": known_skills,
        "gap_skills": gap_skills,
        "market_frequency": frequency,
        "skill_trends": trends,
        "similar_jobs": similar_jobs(db_path, target_skills, keyword),
        "project_scores": projects,
        "resource_plan": recommend_resources(db_path, planning_skills),
        "coverage_matrix": project_coverage_matrix(projects, planning_skills),
    }
