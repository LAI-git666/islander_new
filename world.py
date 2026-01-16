# world.py
import config
from agent import Agent
from data_types import Event

class World:
    def __init__(self):
        self.turn = 0
        self.grid = [[0 for _ in range(config.GRID_SIZE)] for _ in range(config.GRID_SIZE)]
        self.agents = []
        self._init_agents()

    def _init_agents(self):
        # 初始化 3 个不同阶级和人格的 Agent
        self.agents.append(Agent("Kai", "Aggressive", "Poor", 0, 0, config.ENERGY_INIT, config.INITIAL_RESOURCES["POOR"]))
        self.agents.append(Agent("Elala", "Altruistic", "Middle", 5, 5, config.ENERGY_INIT, config.INITIAL_RESOURCES["MIDDLE"]))
        self.agents.append(Agent("Jax", "Dominant", "Rich", 9, 9, config.ENERGY_INIT, config.INITIAL_RESOURCES["RICH"]))

    def get_agent_by_name(self, name):
        for a in self.agents:
            if a.name == name:
                return a
        return None

    def get_all_agent_positions(self):
        """返回全图 GPS 信息 (上帝视角位置)，严禁返回数值状态"""
        return ", ".join([f"{a.name} at ({a.x},{a.y})" for a in self.agents if not a.is_dead])

    def broadcast_events(self, current_turn_events):
        for agent in self.agents:
            if not agent.is_dead:
                agent.perceive(current_turn_events)
                
    def spawn_resources(self):
        """根据配置生成资源"""
        if config.SCARCITY_MODE == "ABUNDANCE":
            tx, ty = config.RESOURCE_SPAWN_LOC
            self.grid[tx][ty] += 1
            return Event(self.turn, "spawn", "SYSTEM", location=(tx, ty), content="Food spawned", success=True, importance_score=3)
        # FAMINE 模式返回 None
        return None