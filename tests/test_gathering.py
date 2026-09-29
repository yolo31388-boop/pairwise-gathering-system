"""采集与加工系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gathering.system import GatheringSystem, GatheringNode, CraftRecipe

class TestRespawnVariance:
    def test_respawn_has_random_variance(self):
        gs = GatheringSystem(seed=42)
        node = GatheringNode("n1", "ore", base_respawn=300)
        times = [gs.get_respawn_time(node) for _ in range(10)]
        assert len(set(times)) > 1  # bug1: 都是300

class TestToolQuality:
    def test_better_tool_improves_success(self):
        gs = GatheringSystem()
        r1 = gs.get_success_rate(skill=50, tool_quality=1)
        r10 = gs.get_success_rate(skill=50, tool_quality=10)
        assert r10 > r1  # bug2: 一样

class TestRecipeUnlock:
    def test_recipe_requires_skill_level(self):
        gs = GatheringSystem()
        gs.recipes["r1"] = CraftRecipe("r1", "legendary", skill_required=50)
        assert gs.can_craft("r1", skill=10) == False  # bug3: True
        assert gs.can_craft("r1", skill=60) == True

class TestInterruption:
    def test_mobs_increase_interruption(self):
        gs = GatheringSystem()
        node = GatheringNode("n1", "ore")
        c0 = gs.get_interruption_chance(node, nearby_mobs=0)
        c5 = gs.get_interruption_chance(node, nearby_mobs=5)
        assert c5 > c0  # bug4: 都是0

class TestOutputQuality:
    def test_better_materials_yield_better_output(self):
        gs = GatheringSystem()
        q1 = gs.get_output_quality({"mat": "normal"})
        q2 = gs.get_output_quality({"mat": "perfect"})
        assert q2 != q1  # bug5: 都是normal

class TestDailyLimit:
    def test_daily_harvest_limit_enforced(self):
        gs = GatheringSystem()
        node = GatheringNode("n1", "ore", daily_limit=5, harvested_today=5)
        assert gs.can_harvest(node) == False  # bug6: True

class TestFailureRefund:
    def test_failure_preserves_rare_materials(self):
        gs = GatheringSystem()
        result = gs.process_failure({"common_mat": 10}, ["rare_mat"])
        assert "rare_mat" in result  # bug7: 空字典
