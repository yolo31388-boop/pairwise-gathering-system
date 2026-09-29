"""采集与加工系统 - 含7个bug"""
import random
from dataclasses import dataclass, field

@dataclass
class GatheringNode:
    nid: str
    type: str
    base_respawn: float = 300
    last_harvest: float = 0
    daily_limit: int = 999  # bug6: 无限制
    harvested_today: int = 0

@dataclass
class CraftRecipe:
    rid: str
    name: str
    skill_required: int = 1
    materials: dict = field(default_factory=dict)
    output: str = ""
    output_qty: int = 1

class GatheringSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.nodes: dict[str, GatheringNode] = {}
        self.recipes: dict[str, CraftRecipe] = {}

    def get_respawn_time(self, node: GatheringNode) -> float:
        # bug1: 固定刷新
        return node.base_respawn

    def get_success_rate(self, skill: int, tool_quality: int) -> float:
        # bug2: 只看技能
        return min(1.0, skill / 100)

    def can_craft(self, recipe_id: str, skill: int) -> bool:
        # bug3: 无解锁条件
        return recipe_id in self.recipes

    def get_interruption_chance(self, node: GatheringNode, nearby_mobs: int) -> float:
        # bug4: 无干扰
        return 0.0

    def get_output_quality(self, materials_quality: dict) -> str:
        # bug5: 产出固定
        return "normal"

    def can_harvest(self, node: GatheringNode) -> bool:
        # bug6: 无每日上限
        return True

    def process_failure(self, materials: dict, rare_materials: list) -> dict:
        # bug7: 材料全消失
        return {}
