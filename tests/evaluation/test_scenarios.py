"""
Unit tests for benchmark scenario generators and serialization.
"""

from pathlib import Path
import tempfile
import pytest

from manigit.evaluation.models import ScenarioCategory
from manigit.evaluation.scenarios import (
    create_decisions_scenario,
    create_distractor_scenario,
    create_duplicate_scenario,
    create_exact_constraints_scenario,
    create_long_conversation_scenario,
    create_stable_facts_scenario,
    create_superseding_facts_scenario,
    create_technical_facts_scenario,
    get_standard_benchmark_suite,
    load_scenario_from_disk,
    save_scenario_to_disk,
)


def test_scenario_creation_all_types():
    suite = get_standard_benchmark_suite()
    assert "stable_facts" in suite
    assert "superseding_facts" in suite
    assert "exact_constraints" in suite
    assert "decisions" in suite
    assert "technical_facts" in suite
    assert "distractors" in suite
    assert "duplicates" in suite
    assert "long_50" in suite
    assert "long_100" in suite

    for key, scenario in suite.items():
        assert scenario.scenario_id is not None
        assert len(scenario.turns) > 0
        assert len(scenario.queries) > 0
        for q in scenario.queries:
            assert q.query_id is not None
            assert len(q.query) > 0
            assert len(q.expected_answer) > 0


def test_stable_facts_scenario():
    sc = create_stable_facts_scenario()
    assert sc.category == ScenarioCategory.STABLE_FACTS
    assert len(sc.queries) == 2
    assert sc.queries[0].expected_answer == "PostgreSQL"
    assert sc.queries[1].expected_answer == "Argon2id"


def test_superseding_facts_scenario():
    sc = create_superseding_facts_scenario()
    assert sc.category == ScenarioCategory.SUPERSEDING_FACTS
    curr_q = next(q for q in sc.queries if not q.is_historical)
    hist_q = next(q for q in sc.queries if q.is_historical)
    assert curr_q.expected_answer == "MongoDB"
    assert hist_q.expected_answer == "PostgreSQL"


def test_exact_constraints_scenario():
    sc = create_exact_constraints_scenario()
    assert sc.category == ScenarioCategory.EXACT_CONSTRAINTS
    timeout_q = next(q for q in sc.queries if q.query_id == "q_exact_timeout")
    assert timeout_q.expected_answer == "500 ms"


def test_decisions_scenario():
    sc = create_decisions_scenario()
    assert sc.category == ScenarioCategory.DECISIONS
    auth_q = next(q for q in sc.queries if q.query_id == "q_decision_auth")
    assert auth_q.expected_answer == "JWT authentication"


def test_technical_facts_scenario():
    sc = create_technical_facts_scenario()
    assert sc.category == ScenarioCategory.TECHNICAL_FACTS
    path_q = next(q for q in sc.queries if q.query_id == "q_tech_path")
    assert path_q.expected_answer == "/etc/manigit/runtime.conf"


def test_distractor_scenario():
    sc = create_distractor_scenario(num_distractors=10)
    assert sc.category == ScenarioCategory.DISTRACTORS
    assert len(sc.turns) >= 22
    distractors = [t for t in sc.turns if t.is_distractor]
    assert len(distractors) >= 20


def test_duplicate_scenario():
    sc = create_duplicate_scenario(num_repeats=3)
    assert sc.category == ScenarioCategory.DUPLICATES
    fact_turns = [t for t in sc.turns if t.contains_fact]
    assert len(fact_turns) == 3


def test_long_conversation_scenario_determinism():
    sc1 = create_long_conversation_scenario(total_turns=50, seed=42)
    sc2 = create_long_conversation_scenario(total_turns=50, seed=42)
    assert len(sc1.turns) == len(sc2.turns)
    for t1, t2 in zip(sc1.turns, sc2.turns):
        assert t1.content == t2.content

    # Different seed
    sc3 = create_long_conversation_scenario(total_turns=50, seed=999)
    assert len(sc3.turns) == len(sc1.turns)


def test_scenario_serialization_and_disk_io():
    sc = create_stable_facts_scenario()
    with tempfile.TemporaryDirectory() as tmp_dir:
        saved_path = save_scenario_to_disk(sc, directory=tmp_dir)
        assert saved_path.exists()
        loaded_sc = load_scenario_from_disk(saved_path)

        assert loaded_sc.scenario_id == sc.scenario_id
        assert loaded_sc.category == sc.category
        assert len(loaded_sc.turns) == len(sc.turns)
        assert len(loaded_sc.queries) == len(sc.queries)
        assert loaded_sc.queries[0].expected_answer == sc.queries[0].expected_answer
