"""
全局对话系统
"""
import json
import time
from typing import List, Tuple, Dict

class GlobalDialogSystem:
    def __init__(self):
        self.npc_conversations = []
        self.communication_events = []  # 专门存储communication类型的互动
        self.action_events = []  # 存储行为事件（拾取、赠送等）
        self.max_conversations = 20
        self.max_communication_events = 50
        self.max_action_events = 50

    def extract_speech(self, message: str) -> str:
        """从消息中提取纯粹的对话内容，移除括号内的动作描述"""
        import re
        import json as json_module
        
        # 如果消息看起来像JSON，尝试解析
        if message.strip().startswith('{') or message.strip().startswith('['):
            try:
                # 尝试解析JSON
                data = json_module.loads(message)
                if isinstance(data, dict):
                    # 检查是否是action指令（不应该显示在对话框）
                    if 'action' in data:
                        # 如果是talk action，提取实际的message或details
                        if data.get('action') == 'talk':
                            # 尝试提取嵌套的message
                            if 'params' in data and isinstance(data['params'], dict):
                                msg = data['params'].get('message', '')
                            elif 'message' in data:
                                msg = data.get('message', '')
                            elif 'details' in data:
                                msg = data.get('details', '')
                            else:
                                return ""  # 纯action指令，不显示
                            
                            # 如果提取的内容还是JSON，返回空
                            if msg.strip().startswith('{'):
                                return ""
                            message = msg
                        else:
                            # 其他action（give, gather等）不应该显示在对话框
                            return ""
            except:
                pass  # 不是有效的JSON，继续处理
        
        # 移除方括号内的内容（如 [action], [thought], [speech]）
        cleaned = re.sub(r'\[.*?\]', '', message)
        # 移除圆括号内的内容（如 (思考), (动作)）
        cleaned = re.sub(r'\(.*?\)', '', cleaned)
        # 移除多余的空白和引号
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = cleaned.strip('"\'')
        
        return cleaned if len(cleaned) > 0 else ""

    def add_conversation(self, npc1_name: str, npc2_name: str, message: str):
        timestamp = time.time()
        # 提取纯粹的对话内容
        clean_message = self.extract_speech(message)
        if clean_message:  # 只有当有实际对话内容时才添加
            self.npc_conversations.append((npc1_name, npc2_name, clean_message, timestamp))
            if len(self.npc_conversations) > self.max_conversations:
                self.npc_conversations.pop(0)
            self.save_to_json(npc1_name, npc2_name, clean_message, timestamp)

    def add_communication_event(self, speaker_name: str, listener_name: str, message: str, volume: str):
        """添加communication类型的互动事件"""
        timestamp = time.time()
        event = {
            "timestamp": timestamp,
            "speaker": speaker_name,
            "listener": listener_name,
            "message": message
        }
        self.communication_events.append(event)
        if len(self.communication_events) > self.max_communication_events:
            self.communication_events.pop(0)

    def add_action_event(self, npc_name: str, action_type: str, details: str, target_name: str = None):
        """添加行为事件（拾取、赠送、进食等）"""
        timestamp = time.time()
        event = {
            "timestamp": timestamp,
            "npc": npc_name,
            "action_type": action_type,
            "details": details,
            "target": target_name
        }
        self.action_events.append(event)
        if len(self.action_events) > self.max_action_events:
            self.action_events.pop(0)

    def get_recent_communications(self, limit: int = 10) -> List[Dict]:
        """获取最近的communication事件"""
        return self.communication_events[-limit:]

    def get_recent_actions(self, limit: int = 10) -> List[Dict]:
        """获取最近的行为事件"""
        return self.action_events[-limit:]

    def get_recent_conversations(self, limit: int = 20) -> List[Tuple[str, str, str, float]]:
        """获取最近的对话记录，默认返回最近20条"""
        current_time = time.time()
        # 显示10分钟内的对话，而不是60秒
        recent = [(n1, n2, msg, t) for n1, n2, msg, t in self.npc_conversations
                if current_time - t < 600]
        return recent[-limit:] if len(recent) > limit else recent

    def save_to_json(self, npc1_name: str, npc2_name: str, message: str, timestamp: float):
        """保存对话到JSON文件"""
        conversation_data = {
            "timestamp": timestamp,
            "npc1": npc1_name,
            "npc2": npc2_name,
            "message": message
        }

        try:
            with open("data/conversations.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(conversation_data)

        with open("data/conversations.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)