"""采集与加工系统"""
import random
from dataclasses import dataclass, field

QUALITY_TIERS = ["poor", "normal", "good", "excellent", "masterwork"]
QUALITY_VALUE = {"poor": 1, "normal": 2, "good": 3, "excellent": 4, "perfect": 5, "masterwork": 6}

@dataclass
class GatheringNode:
    nid: str
    type: str
    base_respawn: float = 300
    last_harvest: float = 0
    daily_limit: int = 50  # fix6: 每日采集上限
    harvested_today: int = 0
    hourly_limit: int = 10  # fix6: 每小时采集上限
    harvested_this_hour: int = 0
    hidden_cooldown: float = 0  # fix1: 被采后的隐藏冷却

@dataclass
class CraftRecipe:
    rid: str
    name: str
    skill_required: int = 1
    materials: dict = field(default_factory=dict)
    output: str = ""
    output_qty: int = 1
    prerequisites: list = field(default_factory=list)  # fix3: 前置配方

class GatheringSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.nodes: dict[str, GatheringNode] = {}
        self.recipes: dict[str, CraftRecipe] = {}
        self.completed_recipes: set = set()

    def get_respawn_time(self, node: GatheringNode) -> float:
        # fix1: 基础刷新时间叠加 ±25% 随机波动，被采后附加隐藏冷却
        variance = self.rng.uniform(0.75, 1.25)
        respawn = node.base_respawn * variance
        if node.last_harvest > 0:
            respawn += node.hidden_cooldown
        return respawn

    def on_harvested(self, node: GatheringNode, now: float) -> None:
        # fix1: 采集后生成玩家不可见的隐藏冷却
        node.last_harvest = now
        node.hidden_cooldown = self.rng.uniform(0, node.base_respawn * 0.3)
        node.harvested_today += 1
        node.harvested_this_hour += 1

    def get_success_rate(self, skill: int, tool_quality: int, env_bonus: float = 0.0) -> float:
        # fix2: 技能等级权重 + 工具品质权重 + 环境加成
        skill_part = skill / 100 * 0.5
        tool_part = tool_quality / 10 * 0.4
        return max(0.0, min(1.0, skill_part + tool_part + env_bonus))

    def can_craft(self, recipe_id: str, skill: int) -> bool:
        # fix3: 需要技能等级达标且前置配方已解锁
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return False
        if skill < recipe.skill_required:
            return False
        return all(pre in self.completed_recipes for pre in recipe.prerequisites)

    def get_interruption_chance(self, node: GatheringNode, nearby_mobs: int) -> float:
        # fix4: 附近怪物提升失败/被打断概率
        return min(0.95, 0.05 + 0.12 * nearby_mobs)

    def get_output_quality(self, materials_quality: dict) -> str:
        # fix5: 产出品质随材料品质浮动，完美材料有概率出极品
        if not materials_quality:
            return "normal"
        values = [QUALITY_VALUE.get(q, 2) for q in materials_quality.values()]
        avg = sum(values) / len(values)
        if avg >= QUALITY_VALUE["perfect"]:
            # 完美材料：30% 概率出杰作，否则保底精良
            return "masterwork" if self.rng.random() < 0.3 else "excellent"
        idx = int(round(avg)) - 1
        idx = max(0, min(len(QUALITY_TIERS) - 1, idx))
        return QUALITY_TIERS[idx]

    def can_harvest(self, node: GatheringNode) -> bool:
        # fix6: 达到每日/每小时上限后需等待刷新重置
        if node.harvested_today >= node.daily_limit:
            return False
        if node.harvested_this_hour >= node.hourly_limit:
            return False
        return True

    def process_failure(self, materials: dict, rare_materials: list) -> dict:
        # fix7: 失败返还部分普通材料，稀有材料保底全返
        returned = {}
        for name, qty in materials.items():
            if name in rare_materials:
                returned[name] = qty  # 稀有材料保底不损失
            else:
                kept = qty // 2  # 普通材料返还一半
                if kept > 0:
                    returned[name] = kept
        for name in rare_materials:
            returned.setdefault(name, 1)
        return returned
