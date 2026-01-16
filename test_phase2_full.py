# test_phase2_full.py (增强版)
from world import World
from action_handler import ActionHandler
from data_types import Event
import config

def run_brain_integration_test():
    print("🧠 Starting Phase 2: Full AI Brain Integration Test (Enhanced)...\n")
    
    world = World()
    handler = ActionHandler()
    kai = world.get_agent_by_name("Kai")     
    elala = world.get_agent_by_name("Elala") 
    
    # ================= SCENARIO 1: 饥饿+仇恨测试 =================
    print("--- SCENARIO 1: Hungry & Vengeful ---")
    
    # 设定：Kai 很饿，且被抢过，且脚下没资源
    kai.x, kai.y = 2, 2
    elala.x, elala.y = 2, 3
    kai.energy = 40  # < 50 触发 Aggressive 阈值
    kai.inventory = 0
    world.grid[2][2] = 0 # 脚下没吃的，逼他别 gather
    
    # 注入仇恨记忆
    fake_event = Event(turn=0, type="rob", agent_name="Elala", target_name="Kai", success=True)
    kai.memory.add_event_from_broadcast(fake_event)
    
    print(f"Status: Kai (Energy 40, Hungry) at 2,2. Elala at 2,3.")
    print(f"Environment: No food at 2,2.")
    
    print("Thinking...")
    decision = kai.think_and_act(world)
    
    print("\n[AI Output]:")
    print(decision)
    
    # 验证
    if decision['action'] in ['rob', 'talk']:
        print("✅ PASS: Kai chose violence/threat due to hunger & revenge.")
    else:
        print(f"⚠️ Result: {decision['action']}. Thought: {decision.get('thought')}")

    # ================= SCENARIO 2: 远程追击测试 =================
    print("\n--- SCENARIO 2: Long Distance Pursuit ---")
    
    # 设定：Kai 极度饥饿，Elala 跑远了，但她是唯一的“食物来源”
    elala.x, elala.y = 8, 8
    kai.memory.memories.append("我看到 Elala 在 (8,8) 手里拿着食物。") # 强行植入信息提示
    
    print(f"Status: Kai at {kai.x},{kai.y}. Elala at {elala.x},{elala.y}.")
    
    print("Thinking...")
    decision = kai.think_and_act(world)
    
    print("\n[AI Output]:")
    print(decision)
    
    target_coords = decision.get("target_coords")
    
    # 只要 AI 决定移动去 (8,8) 就算成功
    if target_coords == [8, 8]:
        print("✅ PASS: AI correctly targeted Elala's coordinates.")
        event = handler.execute(world, kai, decision)
        if event.type == "move":
            print("✅ PASS: ActionHandler converted it to MOVE.")
    else:
        # 如果 AI 还是决定 idle 或者乱走
        print(f"❌ FAIL/SKIP: AI target {target_coords} != [8,8]. Thought: {decision.get('thought')}")

if __name__ == "__main__":
    run_brain_integration_test()