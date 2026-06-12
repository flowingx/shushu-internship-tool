# 求职数据分析智能体

基于 LangChain + SQLite + llama.cpp 的求职市场自然语言分析系统。
在 shushu-internship-tool（鼠鼠实习妙妙工具）开源项目基础上改造。

## 功能特性

- **自然语言查询**：输入中文问题，自动生成 SQL 查询求职数据
- **市场热度分析**：技能需求排名、趋势评分
- **地域分布**：各省市岗位分布
- **薪资分析**：不同类目/经验的薪资对比
- **技能匹配**：岗位所需技能分析

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成数据库（200条岗位数据）
python scripts/generate_job_data.py

# 3. 生成可视化图表
python scripts/visualize.py

# 4. 启动 LLM 服务
python start_server.py

# 5. 测试 Agent
python scripts/data_agent.py --question "哪些技能最热门？"

# 6. 启动 Web 界面
streamlit run app.py
```

## 数据库结构

| 表名 | 说明 |
|------|------|
| raw_jobs | 岗位信息（200条） |
| job_skill_map | 岗位-技能映射 |
| project_templates | 项目模板 |
| project_skill_map | 项目-技能映射 |
| learning_resources | 学习资源 |
| skill_trends | 技能趋势 |

## 项目结构

```
data_agent_project/
├── data/charts/          # 可视化图表
├── db/careers.db         # SQLite 数据库
├── models/               # Qwen3-4B 模型
├── scripts/
│   ├── generate_job_data.py  # 数据生成
│   ├── data_agent.py         # LangChain Agent
│   └── visualize.py          # 可视化
├── app.py                # Streamlit 界面
├── start_server.py       # llama-server 启动
└── requirements.txt
```
