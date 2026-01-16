from data_types import Event
import utils

class MemoryStream:
    def __init__(self, owner_name):
        self.owner_name = owner_name 
        # 存储结构化记忆: [{"text": str, "score": int, "turn": int}, ...]
        self.memories = []

    def add_event_from_broadcast(self, event: Event):
        """将客观事件翻译为主观记忆 (Rashomon Effect)"""
        memory_text = ""
        
        # 视角 A: 我是发起者
        if event.agent_name == self.owner_name:
            if event.type == "rob":
                res = "成功" if event.success else "失败"
                memory_text = f"[Turn {event.turn}] 我抢劫了 {event.target_name}，结果: {res}。"
            elif event.type == "give":
                memory_text = f"[Turn {event.turn}] 我给了 {event.target_name} 食物。"
            elif event.type == "talk":
                memory_text = f"[Turn {event.turn}] 我对 {event.target_name} 说: '{event.content}'"
            elif event.type == "gather":
                 res = "成功" if event.success else "失败"
                 memory_text = f"[Turn {event.turn}] 我尝试采集，结果: {res}。"

        # 视角 B: 我是受害者/接收者
        elif event.target_name == self.owner_name:
            if event.type == "rob":
                res = "被抢了" if event.success else "没被抢"
                memory_text = f"[Turn {event.turn}] {event.agent_name} 试图抢我，结果: {res}。"
            elif event.type == "give":
                memory_text = f"[Turn {event.turn}] {event.agent_name} 给了我食物。"
            elif event.type == "talk":
                memory_text = f"[Turn {event.turn}] {event.agent_name} 对我说: '{event.content}'"
        
        # 视角 C: 旁观者
        else:
            if event.type in ["rob", "give", "talk"]:
                 memory_text = f"[Turn {event.turn}] 看到 {event.agent_name} 对 {event.target_name} 执行了 {event.type}。"

        # 如果生成了记忆文本，将其封装为结构化数据存入
        if memory_text: 
            self.memories.append({
                "text": memory_text,
                "score": event.importance_score, # 从 Event 获取分数
                "turn": event.turn
            })

    def retrieve(self) -> str:
        """
        混合检索策略：
        1. 获取最近的 5 条 (Recency)
        2. 获取历史中分数最高的 5 条 (Importance)
        3. 去重并按时间排序
        """
        if not self.memories:
            return "暂无记忆。"

        # 1. Recency: 最近的 5 条
        recent_memories = self.memories[-5:]
        
        # 2. Importance: 从剩余记忆中选出分数最高的 5 条
        # 先排除已经在 recent 里的，避免重复
        history_pool = [m for m in self.memories if m not in recent_memories]
        # 按 score 降序排序，取前 5
        important_memories = sorted(history_pool, key=lambda x: x["score"], reverse=True)[:5]
        
        # 3. 合并
        combined = recent_memories + important_memories
        
        # 4. 按时间 (turn) 重新排序，保证叙事连贯性
        final_selection = sorted(combined, key=lambda x: x["turn"])
        
        # 5. 提取文本并返回
        return "\n".join([m["text"] for m in final_selection])