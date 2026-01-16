# action_handler.py
import config
from data_types import Event

class ActionHandler:
    def execute(self, world, agent, action_json):
        """统一入口：处理移动预判、能量扣除、动作分发。"""
        action_type = action_json.get("action")
        target_coords = action_json.get("target_coords")
        target_name = action_json.get("target_name")
        
        # --- 1. 组合移动逻辑 (Move-then-Act) ---
        # 凡是涉及位置互动的动作，如果目标不在脚下，且AI指定了坐标，系统强制先移动
        if action_type in ["give", "rob", "move", "gather"] and target_coords:
            current_pos = [agent.x, agent.y]
            # 如果目标坐标与当前不同
            if list(target_coords) != current_pos:
                move_event = self._handle_move(world, agent, target_coords)
                
                # 如果用户指令仅仅是 move，或者移动过程中因体力不支失败，直接返回
                if action_type == "move" or not move_event.success:
                    return move_event
                # 移动成功后，代码继续向下执行具体的互动逻辑...

        # --- 2. 互动逻辑 (此时 Agent 物理坐标已到达目标点) ---
        if action_type == "rob":
            return self._handle_rob(world, agent, target_name)
        elif action_type == "give":
            return self._handle_give(world, agent, target_name)
        elif action_type == "gather":
            return self._handle_gather(world, agent)
        elif action_type == "talk":
            return self._handle_talk(agent, target_name, action_json.get("content"))
        elif action_type == "idle":
            return Event(world.turn, "idle", agent.name, location=(agent.x, agent.y), importance_score=0)
        elif action_type == "eat":
            return self._handle_eat(agent)
        elif action_type == "move":
            # 如果走到这里，说明是单纯的原地 move (target_coords == current_pos)
            return Event(world.turn, "idle", agent.name, location=(agent.x, agent.y), details="Already at location", importance_score=0)
            
        return Event(world.turn, "error", agent.name, details=f"Unknown action: {action_type}", importance_score=0)

    def _handle_move(self, world, agent, target_coords):
        cost = config.ACTION_COSTS["move"]
        if agent.energy < cost:
            return Event(world.turn, "move", agent.name, (agent.x, agent.y), success=False, details="No energy", importance_score=1)
        
        # 检查坐标边界 (0-9)
        tx, ty = target_coords
        if not (0 <= tx < config.GRID_SIZE and 0 <= ty < config.GRID_SIZE):
             return Event(world.turn, "move", agent.name, (agent.x, agent.y), success=False, details="Out of bounds", importance_score=1)

        old_loc = (agent.x, agent.y)
        agent.x, agent.y = tx, ty
        agent.energy -= cost
        
        return Event(world.turn, "move", agent.name, (agent.x, agent.y), success=True, details=f"From {old_loc}", importance_score=1)

    def _handle_rob(self, world, agent, target_name):
        target = world.get_agent_by_name(target_name)
        if not target:
             return Event(world.turn, "rob", agent.name, target_name, success=False, details="Target not found", importance_score=1)

        # 基础消耗 (无论成败都要扣)
        base_cost = config.ACTION_COSTS["rob"]
        
        # 确定性判定：能量碾压
        is_success = agent.energy > target.energy
        
        details = ""
        if is_success:
            # 成功：扣除基础消耗
            agent.energy -= base_cost
            
            if target.inventory > 0:
                agent.inventory += 1
                target.inventory -= 1
                details = "Success (Energy Dominance)"
            else:
                # 赢了但没抢到东西
                is_success = False 
                details = "Success but Target Empty"
        else:
            # 失败：扣除双倍消耗 (基础 + 惩罚)
            agent.energy -= (base_cost * 2) 
            details = "Failed (Energy Insufficient)"
            
        return Event(world.turn, "rob", agent.name, target_name, (agent.x, agent.y), 
                     success=is_success, details=details, importance_score=10)

    def _handle_give(self, world, agent, target_name):
        target_agent = world.get_agent_by_name(target_name)
        if not target_agent:
             return Event(world.turn, "give", agent.name, target_name, success=False, details="Target not found", importance_score=1)

        if (agent.x, agent.y) != (target_agent.x, target_agent.y):
             return Event(world.turn, "give", agent.name, target_name, (agent.x, agent.y), success=False, details="Target not here", importance_score=1)

        if agent.inventory <= 0:
            return Event(world.turn, "give", agent.name, target_name, (agent.x, agent.y), success=False, details="Inventory empty", importance_score=1)

        agent.inventory -= 1
        target_agent.inventory += 1
        agent.energy -= config.ACTION_COSTS["give"]
        return Event(world.turn, "give", agent.name, target_name, (agent.x, agent.y), success=True, importance_score=8)

    def _handle_gather(self, world, agent):
        if world.grid[agent.x][agent.y] > 0:
            if agent.inventory < config.INVENTORY_CAPACITY:
                agent.inventory += 1
                world.grid[agent.x][agent.y] -= 1
                agent.energy -= config.ACTION_COSTS["gather"]
                return Event(world.turn, "gather", agent.name, (agent.x, agent.y), success=True, importance_score=5)
            else:
                return Event(world.turn, "gather", agent.name, (agent.x, agent.y), success=False, details="Inventory Full", importance_score=2)
        return Event(world.turn, "gather", agent.name, (agent.x, agent.y), success=False, details="No food here", importance_score=1)

    def _handle_talk(self, agent, target_name, content):
        agent.energy -= config.ACTION_COSTS["talk"]
        return Event(0, "talk", agent.name, target_name, (agent.x, agent.y), content=content, importance_score=6)

    def _handle_eat(self, agent):
        if agent.inventory > 0:
            agent.inventory -= 1
            agent.energy += config.ENERGY_GAIN_EAT
            return Event(0, "eat", agent.name, location=(agent.x, agent.y), success=True, importance_score=3)
        return Event(0, "eat", agent.name, location=(agent.x, agent.y), success=False, details="No food", importance_score=1)