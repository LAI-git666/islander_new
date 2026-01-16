import concurrent.futures
import config
import utils
from world import World
from action_handler import ActionHandler
from data_types import Event
from dataclasses import asdict
import time
import os

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

def save_individual_memories(turn, agents):
    """
    为每个 Agent 生成独立的记忆日志文件 (JSONL格式)。
    文件路径: logs/memory_{name}.jsonl
    """
    # 确保 logs 目录存在
    if not os.path.exists("logs"):
        os.makedirs("logs")

    for agent in agents:
        filename = f"logs/memory_{agent.name}.jsonl"
        
        # 记录两部分：
        # 1. what_agent_saw: Agent 本回合思考时实际从 retrieve() 获取到的文本
        # 2. full_database: 此时此刻所有的记忆库快照
        
        log_entry = {
            "turn": turn,
            "memory_count": len(agent.memory.memories),
            "what_agent_saw": agent.memory.retrieve(), 
            "full_database": agent.memory.memories 
        }
        
        utils.append_log(filename, log_entry)

def main():
    print("🚀 Initializing DeepSocial-Sim World...")
    world = World()
    agents = world.agents
    action_handler = ActionHandler()
    current_turn_events = [] 

    # --- 清理旧日志 ---
    print("🧹 Cleaning old logs...")
    open("experiment_log.jsonl", "w").close()
    
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # 预先清空每个 agent 的记忆文件
    for agent in agents:
        fpath = f"logs/memory_{agent.name}.jsonl"
        if os.path.exists(fpath):
            open(fpath, "w").close()
    # ----------------

    print(f"👥 Agents Loaded: {[a.name for a in agents]}")
    print(f"🌍 Scarcity Mode: {config.SCARCITY_MODE}")
    print(f"⏳ Max Turns: {config.MAX_TURNS}\n")

    for turn in range(config.MAX_TURNS):
        print(f"--- [Turn {turn}] Start ---")
        world.turn = turn

        # --- Phase 1: 广播上一轮事件 (转化为记忆) ---
        if turn > 0: 
            if current_turn_events:
                print(f"📡 Broadcasting {len(current_turn_events)} events...")
                world.broadcast_events(current_turn_events)
            else:
                print("📡 No events to broadcast.")
        
        current_turn_events = [] 

        # --- Phase 2: 环境刷新 ---
        spawn_event = world.spawn_resources()
        if spawn_event: 
            print("🌱 Resource Spawned!")
            current_turn_events.append(spawn_event)

        # --- Phase 3: 并发思考 (AI Brain) ---
        print("🧠 Agents are thinking...")
        decisions = {}
        active_agents = [a for a in agents if not a.is_dead]
        
        if not active_agents:
            print("💀 All agents are dead. Simulation End.")
            break

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(agent.think_and_act, world): agent for agent in active_agents}
            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                try:
                    res = future.result()
                    decisions[agent.name] = res
                except Exception as e:
                    print(f"❌ Error {agent.name}: {e}")
                    decisions[agent.name] = {"action": "idle", "thought": "Error thinking"}
        
        duration = time.time() - start_time
        print(f"🧠 Thinking finished in {duration:.2f}s")

        # --- Phase 4: 物理执行 (Physics) ---
        print("⚡ Executing Actions...")
        for agent in agents:
            if agent.is_dead: continue
            
            decision = decisions.get(agent.name, {"action": "idle"})
            action_type = decision.get("action")
            target = decision.get("target_name") or decision.get("target_coords") or ""
            
            # 打印简要日志到控制台
            print(f" > {agent.name} ({agent.energy}E): {action_type} -> {target}")
            
            # 执行并获取结果事件
            event = action_handler.execute(world, agent, decision)
            current_turn_events.append(event)
            
            # 额外的控制台可视化
            if event.type == "talk":
                # 截取前50个字符避免刷屏
                content_preview = (event.content[:50] + '...') if len(event.content) > 50 else event.content
                print(f"   💬 \"{content_preview}\"")
            elif event.type == "rob" and event.success:
                print(f"   ⚔️ ROB SUCCESS!")
            elif event.type == "move" and event.success:
                 print(f"   👣 Moved to {agent.x},{agent.y}")

        # --- Phase 5: 代谢与统计 (Metabolism) ---
        for agent in agents:
            if not agent.is_dead:
                agent.energy -= config.METABOLISM_COST
                if agent.energy <= 0:
                    agent.is_dead = True
                    print(f"💀💀💀 {agent.name} DIED of starvation! 💀💀💀")
                    current_turn_events.append(Event(turn, "death", agent.name, location=(agent.x, agent.y), importance_score=10))

        # --- Phase 6: 日志 (Logging) ---
        # 1. 保存全局日志
        save_turn_log(turn, agents, decisions, current_turn_events)
        
        # 2. 保存每个人的私有记忆日志 (新增)
        save_individual_memories(turn, agents)
        
        print(f"--- [Turn {turn}] End ---\n")
        
    print("🎉 Simulation Finished.")
    print("📂 Global Log: 'experiment_log.jsonl'")
    print("📂 Memory Logs: 'logs/memory_*.jsonl'")

if __name__ == "__main__":
    main()