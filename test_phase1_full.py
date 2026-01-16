from world import World
from action_handler import ActionHandler
import config

def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

def print_agent(agent):
    print(f" > [{agent.name}] Pos:({agent.x},{agent.y}) | Energy:{agent.energy} | Inv:{agent.inventory}")

def run_full_test():
    print("🚀 Starting Phase 1 Full Physics Test...")
    
    # 初始化
    world = World()
    handler = ActionHandler()
    
    # 获取测试对象
    kai = world.get_agent_by_name("Kai")   # Poor, (0,0), Inv:0
    elala = world.get_agent_by_name("Elala") # Middle, (5,5), Inv:3
    
    # ================= TEST 1: IDLE =================
    print_separator("TEST 1: Idle (待机)")
    print_agent(kai)
    
    action = {"action": "idle"}
    event = handler.execute(world, kai, action)
    
    print(f"Result: {event.type} | Details: {event.details}")
    print_agent(kai)
    # 预期: 位置不变，能量不变 (idle消耗为0)

    # ================= TEST 2: MOVE =================
    print_separator("TEST 2: Move (基础移动)")
    # 移动到 (0,1)
    action = {"action": "move", "target_coords": [0, 1]}
    event = handler.execute(world, kai, action)
    
    print(f"Result: {event.type} | Success: {event.success}")
    print_agent(kai)
    # 预期: Pos:(0,1), Energy: 98 (100-2)

    # ================= TEST 3: GATHER (Move-then-Act) =================
    print_separator("TEST 3: Gather (远程采集)")
    # 设定 (0,2) 有资源
    world.grid[0][2] = 1
    print(f"Map Resource at (0,2): {world.grid[0][2]}")
    
    # Kai 在 (0,1)，要去 (0,2) 采集
    action = {"action": "gather", "target_coords": [0, 2]}
    event = handler.execute(world, kai, action)
    
    # 逻辑: 先 Move 到 (0,2) (-2能)，再 Gather (-5能)，Inv+1
    print(f"Result: {event.type} | Success: {event.success}")
    print_agent(kai)
    print(f"Map Resource at (0,2): {world.grid[0][2]}")
    # 预期: Pos:(0,2), Energy: 91 (98-2-5), Inv: 1, MapRes: 0

    # ================= TEST 4: EAT =================
    print_separator("TEST 4: Eat (进食)")
    # Kai 现在有 1 个食物 (刚刚采的)，能量 91
    action = {"action": "eat"}
    event = handler.execute(world, kai, action)
    
    print(f"Result: {event.type} | Success: {event.success}")
    print_agent(kai)
    # 预期: Inv: 0, Energy: 121 (91+30)

    # ================= TEST 5: TALK =================
    print_separator("TEST 5: Talk (对话)")
    action = {"action": "talk", "target_name": "Elala", "content": "Hello!"}
    event = handler.execute(world, kai, action)
    
    print(f"Result: {event.type} | Content: {event.content}")
    print_agent(kai)
    # 预期: Energy: 120 (121-1)

    # ================= TEST 6: GIVE (Move-then-Act) =================
    print_separator("TEST 6: Give (远程赠予)")
    # 为了测试 Give，先把 Elala 瞬移到 (0,5)，Kai 在 (0,2)
    elala.x, elala.y = 0, 5
    # 给 Kai 一个食物用于赠送
    kai.inventory = 1 
    
    print("Before Give:")
    print_agent(kai)
    print_agent(elala)
    
    # Kai 走去 (0,5) 给 Elala
    action = {"action": "give", "target_name": "Elala", "target_coords": [0, 5]}
    event = handler.execute(world, kai, action)
    
    # 逻辑: Kai 走3步? 不，我们的逻辑是一步到位瞬间移动
    # 距离不管多远，handle_move 目前逻辑是一步到位扣2能
    # Move (-2) -> (0,5), Give (-1) -> Inv-1
    print(f"Result: {event.type} | Success: {event.success}")
    print_agent(kai)
    print_agent(elala)
    # 预期: Kai Pos:(0,5), Energy: 117 (120-2-1), Inv: 0
    #      Elala Inv: 4 (3+1)

    # ================= TEST 7: ROB (Move-then-Act & 失败判定) =================
    print_separator("TEST 7: Rob (抢劫失败)")
    # 此时两人都在 (0,5)
    # Kai 能量 117, Elala 能量 100 (初始)
    # 为了测试失败，我们把 Kai 能量改低
    kai.energy = 50 
    print("Modified Kai Energy to 50 (Weaker than Elala)")
    
    # 原地抢劫 (target_coords 可以省略或者填当前位置)
    action = {"action": "rob", "target_name": "Elala", "target_coords": [0, 5]}
    event = handler.execute(world, kai, action)
    
    print(f"Result: {event.type} | Success: {event.success} | Details: {event.details}")
    print_agent(kai)
    print_agent(elala)
    # 预期: 判定 50 > 100 False. 失败惩罚 -15.
    # Kai Energy: 35 (50-15). Inv: 0.

    # ================= TEST 8: ROB (成功判定) =================
    print_separator("TEST 8: Rob (抢劫成功)")
    # Kai 怒了，开挂
    kai.energy = 200
    print("Modified Kai Energy to 200 (Stronger)")
    
    event = handler.execute(world, kai, action)
    
    print(f"Result: {event.type} | Success: {event.success} | Details: {event.details}")
    print_agent(kai)
    print_agent(elala)
    # 预期: 判定 200 > 100 True.
    # Kai Inv: 1 (0+1). Elala Inv: 3 (4-1).

    print("\n✅ Full Physics Test Completed.")

if __name__ == "__main__":
    run_full_test()