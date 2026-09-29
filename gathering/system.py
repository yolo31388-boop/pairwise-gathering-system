"""采集与加工系统"""
import random
from dataclasses import dataclass, field

@dataclass
class GatheringNode:
    nid: str
    type: str
    base_respawn: float = 300
    last_harvest: float = 0
    daily_limit: int = 20
    harvested_today: int = 0

@dataclass
class CraftRecipe:
    rid: str
    name: str
    skill_required: int = 1
    materials: dict = field(default_factory=dict)
    output: str = ""
    output_qty: int = 1
    prerequisites: list = field(default_factory=list)

QUALITY_SCORE = {"poor": 0, "normal": 1, "good": 2, "excellent": 3, "perfect": 4}
SCORE_QUALITY = {v: k for k, v in QUALITY_SCORE.items()}

class GatheringSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.nodes: dict[str, GatheringNode] = {}
        self.recipes: dict[str, CraftRecipe] = {}
        self.unlocked_recipes: set = set()

    def get_respawn_time(self, node: GatheringNode) -> float:
        # 基础刷新时间带 ±20% 随机波动
        respawn = node.base_respawn * self.rng.uniform(0.8, 1.2)
        # 被采过后追加一段隐藏冷却，玩家无法精确蹲点
        if node.last_harvest > 0:
            respawn += node.base_respawn * self.rng.uniform(0.1, 0.5)
        return respawn

    def get_success_rate(self, skill: int, tool_quality: int, environment_bonus: float = 0.0) -> float:
        # 技能等级权重 60% + 工具品质权重 35% + 环境加成
        rate = (skill / 100) * 0.6 + (tool_quality / 10) * 0.35 + environment_bonus
        return max(0.0, min(1.0, rate))

    def can_craft(self, recipe_id: str, skill: int) -> bool:
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return False
        # 技能等级门槛
        if skill < recipe.skill_required:
            return False
        # 前置配方必须已解锁
        return all(pre in self.unlocked_recipes for pre in recipe.prerequisites)

    def get_interruption_chance(self, node: GatheringNode, nearby_mobs: int) -> float:
        # 附近怪物越多，被打断概率越高
        return min(0.9, nearby_mobs * 0.12)

    def get_output_quality(self, materials_quality: dict) -> str:
        if not materials_quality:
            return "normal"
        scores = [QUALITY_SCORE.get(q, 1) for q in materials_quality.values()]
        avg = sum(scores) / len(scores)
        # 完美材料有概率爆出更高品质产物
        if max(scores) >= QUALITY_SCORE["perfect"] and self.rng.random() < 0.3:
            avg += 1
        return SCORE_QUALITY[min(QUALITY_SCORE["perfect"], round(avg))]

    def can_harvest(self, node: GatheringNode) -> bool:
        # 达到每日采集上限后需等待刷新
        return node.harvested_today < node.daily_limit

    def process_failure(self, materials: dict, rare_materials: list) -> dict:
        refunded = {}
        for name, qty in materials.items():
            if name in rare_materials:
                # 稀有材料保底，全部返还
                refunded[name] = qty
            else:
                # 普通材料保留一部分（约一半）
                kept = qty // 2
                if kept > 0:
                    refunded[name] = kept
        # 稀有材料即使不在投入清单中也保底返还一份
        for name in rare_materials:
            refunded.setdefault(name, materials.get(name, 1))
        return refunded
