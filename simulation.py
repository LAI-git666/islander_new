import concurrent.futures
import config
import utils
from world import World
from action_handler import ActionHandler
from data_types import Event
from dataclasses import asdict
import time
import os
import random

def save_turn_log(turn, agents, decisions, events):
    """保存本回合全局快照到 experiment_log.jsonl"""
    agents_data = []
    for agent in agents:
        decision = decisions.get(agent.name, {})
        agents_data.append({
            "name": agent.name,
            "status": {
                "energy": agent.energy, 
                "inventory": agent.inventory, 
                "loc": [agent.x, agent.y], 
                "dead": agent.is_dead
            },
            "internal": {
                "thought": decision.get("thought"), 
                "intended": decision.get("action")
            },
            "external": decision
        })
    
    # 转换 events 中的 dataclass 为 dict
    events_list = [asdict(e) for e in events]
    
    utils.append_log("experiment_log.jsonl", {
        "turn": turn, 
        "agents": agents_data, 
        "events": events_list
    })

# 存个人记忆的代码（用不到）
# def save_individual_memories(turn, agents):
#     """
#     为每个 Agent 生成独立的记忆日志文件 (JSONL格式)。
#     文件路径: logs/memory_{name}.jsonl
#     """
#     # 确保 logs 目录存在
#     if not os.path.exists("logs"):
#         os.makedirs("logs")

#     for agent in agents:
#         filename = f"logs/memory_{agent.name}.jsonl"
        
#         # 记录两部分：
#         # 1. what_agent_saw: Agent 本回合思考时实际从 retrieve() 获取到的文本
#         # 2. full_database: 此时此刻所有的记忆库快照
        
#         log_entry = {
#             "turn": turn,
#             "memory_count": len(agent.memory.memories),
#             "what_agent_saw": agent.memory.retrieve(), 
#             "full_database": agent.memory.memories 
#         }
        
#         utils.append_log(filename, log_entry)

def run_simulation(run_id, scarcity_mode, personalities, max_turns):
    """
    执行单次完整仿真
    :param run_id: 实验唯一标识 (如 "FAMINE_All_Aggressive_01")
    :param scarcity_mode: "FAMINE" 或 "ABUNDANCE"
    :param personalities: list, 例如 ["Aggressive", "Aggressive", "Aggressive"]
    :param max_turns: int, 最大回合数
    """
    print(f"🚀 Starting Run: {run_id}")
    
    # 🔴 初始化 World 时传入参数
    world = World(scarcity_mode=scarcity_mode, agent_personalities=personalities)
    agents = world.agents
    action_handler = ActionHandler()
    current_turn_events = [] 

    # 🔴 定义该次实验的日志文件路径
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    global_log_path = f"{log_dir}/experiment_{run_id}.jsonl"
    
    # 清空该次实验的旧日志 (如果有)
    open(global_log_path, "w").close()
    
    # # 清空本次涉及的 agent 的记忆日志
    # for agent in agents:
    #     mem_path = f"{log_dir}/memory_{run_id}_{agent.name}.jsonl"
    #     open(mem_path, "w").close()

    # --- 循环开始 ---
    for turn in range(max_turns):
        print(f"  [{run_id}] Turn {turn}...") # 简化打印，避免刷屏
        world.turn = turn

        # ... Phase 1 - Phase 5 逻辑完全保持不变 ...
        # ... (省略中间代码，与之前完全一致) ...
        # ... 
        if turn > 0: world.broadcast_events(current_turn_events)
        current_turn_events = [] 
        spawn_event = world.spawn_resources()
        if spawn_event: current_turn_events.append(spawn_event)
        
        # Phase 3: Thinking
        active_agents = [a for a in agents if not a.is_dead]
        if not active_agents:
            break # 全死光了提前结束

        decisions = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(agent.think_and_act, world): agent for agent in active_agents}
            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                try:
                    decisions[agent.name] = future.result()
                except:
                    decisions[agent.name] = {"action": "idle"}

        # Phase 4: Acting
         # 🔴 2. 修改开始：打乱执行顺序，消除先手优势
        execution_order = agents[:]  # 创建一个副本
        random.shuffle(execution_order) # 随机打乱顺序
        
        for agent in execution_order: # <--- 这里改成遍历 execution_order
            if agent.is_dead: continue
            decision = decisions.get(agent.name, {"action": "idle"})
            event = action_handler.execute(world, agent, decision)
            current_turn_events.append(event)
            
        # Phase 5: Metabolism
        for agent in agents:
            if not agent.is_dead:
                agent.energy -= config.METABOLISM_COST
                if agent.energy <= 0:
                    agent.is_dead = True
                    current_turn_events.append(Event(turn, "death", agent.name, location=(agent.x, agent.y)))

        # 🔴 Phase 6: 日志 (传入新的路径)
        # 我们需要微调 save_turn_log 的逻辑，或者直接在这里写写入逻辑
        # 为了简单，直接在这里调用 utils.append_log
        
        # 1. 组装数据
        agents_data = []
        for agent in agents:
            decision = decisions.get(agent.name, {})
            agents_data.append({
                "name": agent.name,
                "status": {"energy": agent.energy, "inv": agent.inventory, "loc": [agent.x, agent.y], "dead": agent.is_dead},
                "internal": {"thought": decision.get("thought"), "action": decision.get("action")},
                "external": decision
            })
        
        utils.append_log(global_log_path, {
            "turn": turn, 
            "agents": agents_data, 
            "events": [asdict(e) for e in current_turn_events]
        })

        # 2. 保存记忆 (可选，文件会很多)  已注释
        # for agent in agents:
        #    mem_path = f"{log_dir}/memory_{run_id}_{agent.name}.jsonl"
        #    utils.append_log(mem_path, {"turn": turn, "memory": agent.memory.retrieve()})

    print(f"✅ Finished: {run_id}")
        

