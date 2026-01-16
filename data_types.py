# data_types.py
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class AgentState:
    name: str
    personality: str    # Aggressive, Altruistic, Dominant
    social_class: str   # Rich, Middle, Poor
    x: int
    y: int
    energy: int
    inventory: int
    is_dead: bool

@dataclass
class Event:
    turn: int
    type: str           # "rob", "give", "talk", "move", "idle", "spawn", "gather", "death"
    agent_name: str     # 发起者
    target_name: Optional[str] = None # 目标 (人或资源)
    location: Optional[Tuple[int, int]] = None
    content: Optional[str] = None     # 对话内容
    
    # 结果元数据 (用于罗生门记忆翻译)
    success: bool = True 
    details: str = ""   # 例如: "Energy Dominance", "Inventory Empty"
    importance_score: int = 1 # 在 ActionHandler 中直接赋值