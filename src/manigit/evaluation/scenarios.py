"""
Deterministic synthetic benchmark scenario generators for ManiGit evaluation.

Implements scenarios A through H:
- Stable Facts
- Superseding Facts
- Exact Constraints
- Decisions
- Technical Facts
- Distractor-heavy Conversation
- Repeated / Duplicate Information
- Scaled Long Conversations (50, 100, 250+ turns)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import random

from manigit.evaluation.models import (
    BenchmarkQuery,
    BenchmarkScenario,
    ScenarioCategory,
    ScenarioTurn,
)


def create_stable_facts_scenario() -> BenchmarkScenario:
    """Scenario A: Stable facts that do not change over time."""
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="The backend database is PostgreSQL.",
            contains_fact="backend database is PostgreSQL",
            fact_key="database",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Understood. The backend database is set to PostgreSQL.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content="Let us also implement the user registration endpoint.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="I will scaffold the user registration endpoint using our data model.",
        ),
        ScenarioTurn(
            turn_index=4,
            role="user",
            content="Please ensure password hashing uses Argon2id.",
            contains_fact="password hashing uses Argon2id",
            fact_key="hashing",
        ),
        ScenarioTurn(
            turn_index=5,
            role="assistant",
            content="Configured Argon2id for password hashing.",
        ),
        ScenarioTurn(
            turn_index=6,
            role="user",
            content="Let's run the smoke tests now.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=7,
            role="assistant",
            content="Smoke tests passed successfully with 0 errors.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_stable_db",
            query="What database are we using?",
            expected_answer="PostgreSQL",
            acceptable_alternatives=["PostgreSQL database", "postgres"],
            target_fact_key="database",
            relevant_turn_indices=[0, 1],
        ),
        BenchmarkQuery(
            query_id="q_stable_hash",
            query="What hashing algorithm was specified for passwords?",
            expected_answer="Argon2id",
            acceptable_alternatives=["Argon2id hashing", "argon2"],
            target_fact_key="hashing",
            relevant_turn_indices=[4, 5],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_a_stable_facts",
        name="Stable Facts Scenario",
        category=ScenarioCategory.STABLE_FACTS,
        description="Evaluates retention of stable technical configuration across dialogue turns.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def create_superseding_facts_scenario() -> BenchmarkScenario:
    """Scenario B: Facts that are later explicitly superseded."""
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="The backend database is PostgreSQL.",
            contains_fact="backend database is PostgreSQL",
            fact_key="database_v1",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Noted: PostgreSQL will be our backend database.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content="Let's build the preliminary schema migrations.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="Preliminary migrations created.",
        ),
        ScenarioTurn(
            turn_index=4,
            role="user",
            content="We decided to migrate the backend to MongoDB.",
            contains_fact="migrate the backend to MongoDB",
            fact_key="database_v2",
        ),
        ScenarioTurn(
            turn_index=5,
            role="assistant",
            content="Acknowledged. The backend database is now migrated to MongoDB.",
        ),
        ScenarioTurn(
            turn_index=6,
            role="user",
            content="Update the collection connection string accordingly.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=7,
            role="assistant",
            content="Updated connection configuration for MongoDB.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_superseding_current",
            query="What database are we using now?",
            expected_answer="MongoDB",
            acceptable_alternatives=["mongo", "MongoDB database"],
            is_historical=False,
            target_fact_key="database_v2",
            relevant_turn_indices=[4, 5],
        ),
        BenchmarkQuery(
            query_id="q_superseding_historical",
            query="What database was specified before the migration?",
            expected_answer="PostgreSQL",
            acceptable_alternatives=["postgres", "PostgreSQL database"],
            is_historical=True,
            target_commit_ref="commit_initial",
            target_fact_key="database_v1",
            relevant_turn_indices=[0, 1],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_b_superseding_facts",
        name="Superseding Facts Scenario",
        category=ScenarioCategory.SUPERSEDING_FACTS,
        description="Evaluates distinction between active current facts and superseded historical facts.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def create_exact_constraints_scenario() -> BenchmarkScenario:
    """Scenario C: Exact numeric and boundary constraints."""
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="The API timeout must remain below 500 ms.",
            contains_fact="API timeout below 500 ms",
            fact_key="api_timeout",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Understood. The API timeout constraint is strictly 500 ms.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content="The batch processing pool size is limited to 16 workers.",
            contains_fact="batch pool size 16 workers",
            fact_key="pool_size",
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="Worker pool capped at 16.",
        ),
        ScenarioTurn(
            turn_index=4,
            role="user",
            content="Let's optimize the serialization pipeline.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=5,
            role="assistant",
            content="Serialization pipeline optimized.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_exact_timeout",
            query="What is the exact API timeout constraint?",
            expected_answer="500 ms",
            acceptable_alternatives=["500ms", "below 500 ms"],
            target_fact_key="api_timeout",
            relevant_turn_indices=[0, 1],
        ),
        BenchmarkQuery(
            query_id="q_exact_pool",
            query="What is the maximum worker pool size for batch processing?",
            expected_answer="16 workers",
            acceptable_alternatives=["16", "16 workers"],
            target_fact_key="pool_size",
            relevant_turn_indices=[2, 3],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_c_exact_constraints",
        name="Exact Constraints Scenario",
        category=ScenarioCategory.EXACT_CONSTRAINTS,
        description="Evaluates precision of exact numeric and boundary constraints through memory.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def create_decisions_scenario() -> BenchmarkScenario:
    """Scenario D: Architectural and design decisions."""
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="We decided to use JWT authentication rather than session cookies.",
            contains_fact="use JWT authentication rather than session cookies",
            fact_key="auth_decision",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Decision recorded: JWT authentication selected over session cookies.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content="We will adopt event sourcing for the billing domain.",
            contains_fact="adopt event sourcing for the billing domain",
            fact_key="billing_arch",
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="Billing architecture specified as event sourcing.",
        ),
        ScenarioTurn(
            turn_index=4,
            role="user",
            content="Let's review the upcoming release schedule.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=5,
            role="assistant",
            content="Release schedule reviewed.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_decision_auth",
            query="What authentication approach did we decide on?",
            expected_answer="JWT authentication",
            acceptable_alternatives=["JWT", "JWT tokens"],
            target_fact_key="auth_decision",
            relevant_turn_indices=[0, 1],
        ),
        BenchmarkQuery(
            query_id="q_decision_billing",
            query="What architecture did we decide to adopt for the billing domain?",
            expected_answer="event sourcing",
            acceptable_alternatives=["event-sourcing", "Event Sourcing"],
            target_fact_key="billing_arch",
            relevant_turn_indices=[2, 3],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_d_decisions",
        name="Architectural Decisions Scenario",
        category=ScenarioCategory.DECISIONS,
        description="Evaluates retention of explicit architectural and design decisions.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def create_technical_facts_scenario() -> BenchmarkScenario:
    """Scenario E: Technical identifiers, paths, and exact error codes."""
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="The primary configuration file is located at /etc/manigit/runtime.conf.",
            contains_fact="configuration file is located at /etc/manigit/runtime.conf",
            fact_key="conf_path",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Configuration path noted: /etc/manigit/runtime.conf.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content="The upstream socket timeout error code is ERR_SOCKET_TIMEOUT_902.",
            contains_fact="error code is ERR_SOCKET_TIMEOUT_902",
            fact_key="error_code",
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="Noted socket error ERR_SOCKET_TIMEOUT_902.",
        ),
        ScenarioTurn(
            turn_index=4,
            role="user",
            content="The metrics endpoint route is /api/v2/telemetry/events.",
            contains_fact="metrics endpoint route is /api/v2/telemetry/events",
            fact_key="metrics_route",
        ),
        ScenarioTurn(
            turn_index=5,
            role="assistant",
            content="Telemetry endpoint route registered.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_tech_path",
            query="Where is the primary configuration file located?",
            expected_answer="/etc/manigit/runtime.conf",
            acceptable_alternatives=["runtime.conf", "/etc/manigit/runtime.conf"],
            target_fact_key="conf_path",
            relevant_turn_indices=[0, 1],
        ),
        BenchmarkQuery(
            query_id="q_tech_err",
            query="What is the upstream socket timeout error code?",
            expected_answer="ERR_SOCKET_TIMEOUT_902",
            acceptable_alternatives=["ERR_SOCKET_TIMEOUT_902"],
            target_fact_key="error_code",
            relevant_turn_indices=[2, 3],
        ),
        BenchmarkQuery(
            query_id="q_tech_route",
            query="What is the exact route for the telemetry metrics endpoint?",
            expected_answer="/api/v2/telemetry/events",
            acceptable_alternatives=["/api/v2/telemetry/events"],
            target_fact_key="metrics_route",
            relevant_turn_indices=[4, 5],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_e_technical_facts",
        name="Technical Facts & Identifiers Scenario",
        category=ScenarioCategory.TECHNICAL_FACTS,
        description="Evaluates exact retention of code identifiers, paths, and error codes.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def create_distractor_scenario(num_distractors: int = 30) -> BenchmarkScenario:
    """Scenario F: Few critical facts drowned in conversational distractors."""
    turns: List[ScenarioTurn] = []
    
    # Early fact
    turns.append(ScenarioTurn(
        turn_index=0,
        role="user",
        content="The internal caching service port is 6379.",
        contains_fact="caching service port is 6379",
        fact_key="cache_port",
    ))
    turns.append(ScenarioTurn(
        turn_index=1,
        role="assistant",
        content="Internal Redis cache port confirmed at 6379.",
    ))

    distractor_templates = [
        ("Good morning! How is the build server looking today?", "Good morning. The build server is operational."),
        ("Thanks for the update.", "You're very welcome."),
        ("Let me grab a quick coffee before we review the log files.", "Take your time. I am ready when you are."),
        ("Looks like the weather outside is quite cloudy today.", "Indeed, pleasant weather for programming."),
        ("Could you check if the formatting linter ran cleanly?", "The linter reported no warnings."),
        ("Great, thanks.", "Happy to help."),
        ("Let's see what tickets are in the current sprint.", "Sprint backlog contains 12 open tickets."),
        ("Sounds good. Let's keep moving forward.", "Proceeding as planned."),
        ("Did you see the latest commit message?", "Yes, the commit message was clear and concise."),
        ("Awesome.", "Glad to hear."),
    ]

    idx = 2
    for i in range(num_distractors):
        u_tmpl, a_tmpl = distractor_templates[i % len(distractor_templates)]
        turns.append(ScenarioTurn(
            turn_index=idx,
            role="user",
            content=f"[Turn {idx}] {u_tmpl}",
            is_distractor=True,
        ))
        idx += 1
        turns.append(ScenarioTurn(
            turn_index=idx,
            role="assistant",
            content=f"[Turn {idx}] {a_tmpl}",
            is_distractor=True,
        ))
        idx += 1

    # Late fact
    turns.append(ScenarioTurn(
        turn_index=idx,
        role="user",
        content="The staging deployment target cluster is us-central1-k8s-prod.",
        contains_fact="target cluster is us-central1-k8s-prod",
        fact_key="deploy_cluster",
    ))
    idx += 1
    turns.append(ScenarioTurn(
        turn_index=idx,
        role="assistant",
        content="Cluster target us-central1-k8s-prod saved for staging deployment.",
    ))

    queries = [
        BenchmarkQuery(
            query_id="q_distractor_cache",
            query="What port does the internal caching service use?",
            expected_answer="6379",
            acceptable_alternatives=["port 6379"],
            target_fact_key="cache_port",
            relevant_turn_indices=[0, 1],
        ),
        BenchmarkQuery(
            query_id="q_distractor_cluster",
            query="What is the deployment target cluster for staging?",
            expected_answer="us-central1-k8s-prod",
            acceptable_alternatives=["us-central1-k8s-prod cluster"],
            target_fact_key="deploy_cluster",
            relevant_turn_indices=[idx - 1, idx],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_f_distractors",
        name="Distractor-Heavy Conversation Scenario",
        category=ScenarioCategory.DISTRACTORS,
        description="Evaluates needle-in-a-haystack recall when critical facts are buried in conversational noise.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns), "distractors_count": num_distractors * 2},
    )


def create_duplicate_scenario(num_repeats: int = 4) -> BenchmarkScenario:
    """Scenario G: Identical facts repeated multiple times to test redundancy suppression."""
    turns: List[ScenarioTurn] = []
    idx = 0
    for i in range(num_repeats):
        turns.append(ScenarioTurn(
            turn_index=idx,
            role="user",
            content=f"Remember that the default retention window is strictly 90 days. (Reminder {i+1})",
            contains_fact="retention window is strictly 90 days",
            fact_key="retention_window",
        ))
        idx += 1
        turns.append(ScenarioTurn(
            turn_index=idx,
            role="assistant",
            content=f"Understood. Retention window is 90 days. Acknowledged iteration {i+1}.",
        ))
        idx += 1
        # Add a filler turn between duplicates
        turns.append(ScenarioTurn(
            turn_index=idx,
            role="user",
            content=f"Proceed with regular backlog tasks for cycle {i+1}.",
            is_distractor=True,
        ))
        idx += 1
        turns.append(ScenarioTurn(
            turn_index=idx,
            role="assistant",
            content=f"Backlog cycle {i+1} tasks running.",
            is_distractor=True,
        ))
        idx += 1

    queries = [
        BenchmarkQuery(
            query_id="q_duplicate_retention",
            query="What is the default data retention window?",
            expected_answer="90 days",
            acceptable_alternatives=["90 days retention", "90-day"],
            target_fact_key="retention_window",
            relevant_turn_indices=[0, 1],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_g_duplicates",
        name="Duplicate Information Scenario",
        category=ScenarioCategory.DUPLICATES,
        description="Evaluates whether repeated statements bloat context or are efficiently deduplicated.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns), "repeat_count": num_repeats},
    )


def create_long_conversation_scenario(total_turns: int = 50, seed: int = 42) -> BenchmarkScenario:
    """
    Scenario H: Progressively scaled long conversations (50, 100, 250 turns).
    Places distinct critical facts across early, middle, and late conversational phases.
    """
    rng = random.Random(seed)
    turns: List[ScenarioTurn] = []

    # Fact 1 (Early phase: turn 0)
    turns.append(ScenarioTurn(
        turn_index=0,
        role="user",
        content="The infrastructure provider is AWS with region eu-west-1.",
        contains_fact="infrastructure provider is AWS region eu-west-1",
        fact_key="infra_region",
    ))
    turns.append(ScenarioTurn(
        turn_index=1,
        role="assistant",
        content="Configured infrastructure on AWS in eu-west-1.",
    ))

    mid_turn_target = total_turns // 2
    late_turn_target = total_turns - 4

    dialogue_fillers = [
        ("Checking system memory utilization across nodes.", "Memory utilization is nominal at 42%."),
        ("Refactoring the telemetry dispatcher logic.", "Telemetry dispatcher refactored."),
        ("Investigating latency spikes in the message queue.", "Queue latency is steady at 12ms."),
        ("Running unit test suite for billing modules.", "All 45 billing unit tests passed."),
        ("Auditing user permissions for the administrative console.", "Admin permissions verified against RBAC matrix."),
        ("Updating OpenAPI documentation spec for v3.", "OpenAPI spec generated and uploaded."),
        ("Testing backup snapshot creation and restore procedure.", "Snapshot restored successfully to sandbox."),
        ("Reviewing pull request for dependency bump.", "Dependency bump approved without conflicts."),
    ]

    idx = 2
    while idx < total_turns - 2:
        if idx == mid_turn_target:
            # Fact 2 (Mid phase)
            turns.append(ScenarioTurn(
                turn_index=idx,
                role="user",
                content="The primary encryption key identifier is KMS-KEY-ALPHA-77.",
                contains_fact="encryption key identifier is KMS-KEY-ALPHA-77",
                fact_key="kms_key",
            ))
            idx += 1
            turns.append(ScenarioTurn(
                turn_index=idx,
                role="assistant",
                content="Primary encryption key KMS-KEY-ALPHA-77 registered.",
            ))
            idx += 1
        elif idx == late_turn_target:
            # Fact 3 (Late phase)
            turns.append(ScenarioTurn(
                turn_index=idx,
                role="user",
                content="The production deployment freeze starts on 2026-12-15.",
                contains_fact="deployment freeze starts on 2026-12-15",
                fact_key="freeze_date",
            ))
            idx += 1
            turns.append(ScenarioTurn(
                turn_index=idx,
                role="assistant",
                content="Deployment freeze scheduled for 2026-12-15.",
            ))
            idx += 1
        else:
            u_text, a_text = dialogue_fillers[idx % len(dialogue_fillers)]
            turns.append(ScenarioTurn(
                turn_index=idx,
                role="user",
                content=f"[Turn {idx}] {u_text}",
                is_distractor=True,
            ))
            idx += 1
            turns.append(ScenarioTurn(
                turn_index=idx,
                role="assistant",
                content=f"[Turn {idx}] {a_text}",
                is_distractor=True,
            ))
            idx += 1

    queries = [
        BenchmarkQuery(
            query_id="q_long_early_region",
            query="What AWS region is our infrastructure hosted in?",
            expected_answer="eu-west-1",
            acceptable_alternatives=["AWS region eu-west-1", "eu-west-1"],
            target_fact_key="infra_region",
            relevant_turn_indices=[0, 1],
        ),
        BenchmarkQuery(
            query_id="q_long_mid_kms",
            query="What is the primary KMS encryption key identifier?",
            expected_answer="KMS-KEY-ALPHA-77",
            acceptable_alternatives=["KMS-KEY-ALPHA-77"],
            target_fact_key="kms_key",
            relevant_turn_indices=[mid_turn_target, mid_turn_target + 1],
        ),
        BenchmarkQuery(
            query_id="q_long_late_freeze",
            query="When does the production deployment freeze start?",
            expected_answer="2026-12-15",
            acceptable_alternatives=["2026-12-15", "December 15, 2026"],
            target_fact_key="freeze_date",
            relevant_turn_indices=[late_turn_target, late_turn_target + 1],
        ),
    ]

    return BenchmarkScenario(
        scenario_id=f"scenario_h_long_{total_turns}",
        name=f"Long Conversation Scenario ({total_turns} turns)",
        category=ScenarioCategory.LONG_CONVERSATION,
        description=f"Evaluates retention of early, middle, and late critical facts across {total_turns} conversational turns.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns), "seed": seed},
    )


def create_ambiguous_confidence_scenario() -> BenchmarkScenario:
    """
    Scenario I: Ambiguous / Low-Confidence Fact Candidate.
    Designed specifically to evaluate H4 (Confidence-aware classification).
    Tests whether uncertain/tentative information is safely escalated to VERBATIM
    or lost when confidence evaluation is neutralized.
    """
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="Customer noted they might scale to 10k users in Q3, but not certain yet.",
            contains_fact="scale to 10k users",
            fact_key="user_scale",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Understood. Noted the tentative customer scale target of 10k users.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content="Let's check the build status for the staging environment.",
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="Staging build is passing.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_ambiguous_scale",
            query="What user scale did the customer mention for Q3?",
            expected_answer="10k users",
            acceptable_alternatives=["10k", "10,000 users", "scale to 10k users"],
            target_fact_key="user_scale",
            relevant_turn_indices=[0, 1],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_i_ambiguous_confidence",
        name="Ambiguous Confidence Classification Scenario",
        category=ScenarioCategory.AMBIGUOUS_CONFIDENCE,
        description="Evaluates conservative preservation of tentative/ambiguous statements via confidence-aware escalation.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def create_tier_competition_scenario() -> BenchmarkScenario:
    """
    Scenario J: Tier Competition Under Tight Token Budget (B=128).
    Designed specifically to evaluate H5 (Tier-aware context selection).
    A concise critical VERBATIM constraint (15 tokens) competes against a long
    exploratory SUMMARY discussion (85 tokens) under a tight token budget.
    """
    turns = [
        ScenarioTurn(
            turn_index=0,
            role="user",
            content="Egress traffic routes via proxy gateway proxy-gw-01.",
            contains_fact="proxy-gw-01",
            fact_key="egress_proxy",
        ),
        ScenarioTurn(
            turn_index=1,
            role="assistant",
            content="Configured routing rule to enforce proxy-gw-01 for all egress.",
        ),
        ScenarioTurn(
            turn_index=2,
            role="user",
            content=(
                "Detailed gateway cluster architectural review and discussion summary: "
                "We analyzed all egress traffic paths across every gateway proxy node in the infrastructure. "
                "Engineers reviewed proxy routes behaviors, egress traffic bandwidth, gateway latency profiles, "
                "proxy failover topology, packet inspection details, and TLS termination. "
                "Engineers noted that proxy gateway routes for egress traffic have continuous telemetry monitoring."
            ),
            is_distractor=True,
        ),
        ScenarioTurn(
            turn_index=3,
            role="assistant",
            content="Documented the gateway cluster architectural review and discussion.",
        ),
    ]

    queries = [
        BenchmarkQuery(
            query_id="q_tier_egress_proxy",
            query="What proxy gateway routes egress traffic?",
            expected_answer="proxy-gw-01",
            acceptable_alternatives=["proxy-gw-01", "proxy gateway proxy-gw-01", "gateway proxy-gw-01"],
            target_fact_key="egress_proxy",
            relevant_turn_indices=[0, 1],
        ),
    ]

    return BenchmarkScenario(
        scenario_id="scenario_j_tier_competition",
        name="Tier Competition Under Constrained Budget Scenario",
        category=ScenarioCategory.TIER_COMPETITION,
        description="Evaluates tier-aware prioritization of concise verbatim constraints against verbose summaries under tight budgets.",
        turns=turns,
        queries=queries,
        metadata={"total_turns": len(turns)},
    )


def get_standard_benchmark_suite() -> Dict[str, BenchmarkScenario]:
    """Returns the full canonical suite of evaluation scenarios (9 scenarios, 20 queries)."""
    return {
        "stable_facts": create_stable_facts_scenario(),
        "superseding_facts": create_superseding_facts_scenario(),
        "exact_constraints": create_exact_constraints_scenario(),
        "decisions": create_decisions_scenario(),
        "technical_facts": create_technical_facts_scenario(),
        "distractors": create_distractor_scenario(num_distractors=25),
        "duplicates": create_duplicate_scenario(num_repeats=4),
        "long_50": create_long_conversation_scenario(total_turns=50),
        "long_100": create_long_conversation_scenario(total_turns=100),
    }


def get_ablation_benchmark_suite() -> Dict[str, BenchmarkScenario]:
    """
    Returns the comprehensive ablation benchmark suite:
    9 standard scenarios (20 queries) + 2 controlled ablation scenarios (2 queries) = 11 scenarios (22 queries).
    """
    suite = get_standard_benchmark_suite()
    suite["ambiguous_confidence"] = create_ambiguous_confidence_scenario()
    suite["tier_competition"] = create_tier_competition_scenario()
    return suite


def save_scenario_to_disk(scenario: BenchmarkScenario, directory: str = "data/processed/benchmarks/scenarios") -> Path:
    """Saves a BenchmarkScenario instance as a JSON file."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{scenario.scenario_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(scenario.to_dict(), f, indent=2)
    return file_path


def load_scenario_from_disk(file_path: Path) -> BenchmarkScenario:
    """Loads a BenchmarkScenario from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BenchmarkScenario.from_dict(data)
