# Islanders

这是一个为您准备的 `README.md` 文档。您可以直接将其保存到项目根目录下，然后上传到 GitHub。这份文档详细介绍了项目架构、代码功能、运行步骤以及实验修改指南，非常适合您的 Partner 快速上手。

---

# DeepSocial-Sim (Headless)

**DeepSocial-Sim** 是一个由大语言模型（LLM）驱动的多智能体社会仿真系统。它模拟了在一个资源受限（或富足）的封闭环境中，不同人格（利己、利他、支配）的智能体如何通过移动、采集、对话、抢劫和赠予进行生存博弈。

本项目采用 **Headless（无图形界面）** 模式运行，所有行为数据以 JSONL 格式记录，支持深度的数据分析和复盘。

---

## 🛠️ 环境准备

### 1. 依赖安装
本项目基于 Python 3.9+。
```bash
pip install openai
```

### 2. API 配置
项目默认兼容 OpenAI 格式的接口（如阿里云百炼/通义千问、DeepSeek、OpenAI 原生）。
请在 `llm_client.py` 中配置您的 API Key：

```python
# llm_client.py
self.default_api_key = "sk-xxxxxxxx" 
self.default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" # 示例：阿里云
self.default_model = "qwen-plus"
```

---

## 📂 项目结构与代码详解

### 1. 核心逻辑层

*   **`simulation.py` (主程序入口)**
    *   `main()`: 仿真循环的心脏。负责回合推进 (Turn Loop)、事件广播、并发调用 AI 思考、物理动作结算、代谢扣血以及日志保存。
    *   `save_turn_log()`: 保存每回合的全局快照到 `experiment_log.jsonl`。
    *   `save_individual_memories()`: 将每个智能体的私有记忆保存到 `logs/` 文件夹。

*   **`action_handler.py` (物理引擎/裁判)**
    *   `execute(world, agent, action_json)`: 统一处理所有动作请求。
    *   **Move-then-Act 逻辑**: 如果 AI 请求互动（如抢劫）但目标不在脚下，系统会自动让 Agent 先消耗能量移动到目标点。
    *   `_handle_rob`: 执行抢劫。采用**能量确定性判定**（能量高者必胜）。
    *   `_handle_gather/give/move`: 处理资源采集、赠予和移动的数值结算。

*   **`agent.py` (智能体对象)**
    *   `think_and_act(world)`: Agent 的“大脑”。负责收集感知信息（GPS、记忆）、组装 Prompt、调用 LLM 并返回 JSON 决策。
    *   `perceive(events)`: 接收世界广播的事件并写入记忆。

*   **`world.py` (环境容器)**
    *   `get_all_agent_positions()`: 提供全图 GPS 信息（仅名字和坐标，严禁泄露能量/库存）。
    *   `broadcast_events()`: 将上一回合发生的事件分发给所有存活的 Agent。
    *   `spawn_resources()`: 根据稀缺模式在地图上生成食物。

### 2. 数据与工具层

*   **`memory.py` (记忆系统)**
    *   **罗生门效应 (Rashomon Effect)**: `add_event_from_broadcast` 函数会将同一个客观事件（Event）翻译成不同视角的自然语言记忆（我做的/我被做的/我看到的）。
    *   `retrieve()`: 混合检索逻辑。提取“最近发生的5件事” + “历史中印象最深的5件事”。

*   **`llm_client.py` (API 封装)**
    *   `get_response()`: 发送请求给 LLM。包含**正则提取**功能，确保从模型回复中准确提取 JSON 对象，并包含自动重试机制。

*   **`prompts.py` (提示词工程)**
    *   `PERSONALITY_PROMPTS`: 定义了三种人格（Aggressive, Altruistic, Dominant）的第一性原理和决策逻辑。
    *   `get_user_prompt`: 动态生成每一轮的输入，包含 GPS 信息、记忆流和当前状态。

*   **`config.py` (全局配置)**
    *   包含所有数值设定：地图大小、最大回合数、动作能耗表、初始资源等。

*   **`data_types.py` & `utils.py`**
    *   定义数据类 (`AgentState`, `Event`) 和文件 I/O 工具函数。

*   **`log_viewer.py` (日志阅读器)**
    *   一个辅助脚本，用于将难懂的 JSONL 日志渲染成可读性强的“剧本”格式，方便人类查阅。

---

## 🚀 如何运行实验

### 步骤 1: 启动仿真
在终端运行：
```bash
python simulation.py
```
控制台将实时打印每个回合的动作简报。运行结束后，会生成日志文件。

### 步骤 2: 查看结果
**方式 A: 使用阅读器（推荐）**
```bash
python log_viewer.py
```
这将把实验过程渲染成对话剧本。

**方式 B: 查看原始数据**
*   `experiment_log.jsonl`: 包含每一回合所有人的状态、思考和动作。
*   `logs/memory_{Name}.jsonl`: 单独查看某个角色的记忆进化史。

---

## 🧪 实验修改指南 (给 Partner 的 Tips)

如果你想调整实验条件，请修改以下文件：

### 1. 修改“资源稀缺度” (饥荒 vs 富足)
打开 `config.py`:
```python
# 修改此变量
SCARCITY_MODE = "FAMINE"   # 饥荒模式 (不刷新食物)
# SCARCITY_MODE = "ABUNDANCE" # 富足模式 (每回合刷新食物)
```

### 2. 修改“初始人物设定” (阶级/人格)
打开 `world.py` 中的 `_init_agents` 函数:
```python
def _init_agents(self):
    # 格式: Agent(名字, 人格, 阶级, X坐标, Y坐标, 初始能量, 初始库存)
    # 例如：把 Kai 变成富人
    self.agents.append(Agent("Kai", "Aggressive", "Rich", 0, 0, 100, 5))
```

### 3. 修改“物理规则” (动作消耗)
打开 `config.py`:
```python
ACTION_COSTS = {
    "rob": 15,  # 觉得抢劫成本太低？改成 30
    "talk": 1,  # 觉得说话太费劲？改成 0
    ...
}
```

### 4. 修改“实验时长”
打开 `config.py`:
```python
MAX_TURNS = 20 # 增加回合数以观察长期演化
METABOLISM_COST = 5 # 调整每回合掉血速度
```

### 5. 修改“人格提示词” (Prompt Engineering)
打开 `prompts.py`:
直接编辑 `PERSONALITY_PROMPTS` 字典中的文字，可以调整 AI 的性格倾向（例如让 Aggressive 更暴力，或让 Altruistic 更圣母）。

---

## 📊 输出文件说明

*   **experiment_log.jsonl**:
    *   主日志文件。每一行代表一个 Turn。
    *   包含 `internal` (Thought/Intended Action) 和 `external` (Actual Action/Result)。
    *   用于计算 **"伪君子指数"** (Hypocrisy Index)。

*   **logs/memory_{AgentName}.jsonl**:
    *   记录了该 Agent 在每一轮思考时，脑子里究竟“检索”到了哪些记忆 (`what_agent_saw`)。
    *   用于分析 AI 的决策依据。
