# config.py

# 地图与时间
GRID_SIZE = 10          # 10x10 网格
MAX_TURNS = 50         # 实验持续回合数

# 资源生成模式
# "ABUNDANCE": 固定点刷新资源; "FAMINE": 不刷新
SCARCITY_MODE = "FAMINE" 
RESOURCE_SPAWN_LOC = (5, 5) 

# 生存数值 (Metabolism)
ENERGY_INIT = 100
METABOLISM_COST = 5      # 每回合基础扣除
ENERGY_GAIN_EAT = 30     # 进食恢复
INVENTORY_CAPACITY = 5   # 背包上限

# 动作能耗表 (Action Costs)
ACTION_COSTS = {
    "move": 2,          # 基础移动消耗
    "talk": 1,          # 说话消耗 (低成本)
    "gather": 5,        # 采集消耗
    "give": 0,          # 赠予消耗
    "rob": 15,          # 抢劫消耗 (高风险)
    "idle": 0,          # 待机
    "eat": 0            # 进食
}

# 初始资源设定
INITIAL_RESOURCES = {
    "RICH": 5,
    "MIDDLE": 3,
    "POOR": 0

}
