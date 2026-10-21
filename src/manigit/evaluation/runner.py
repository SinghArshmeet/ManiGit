"""
Experiment runner for ManiGit research benchmarking.

Executes experimental matrices across:
- Evaluation methods (Full History, Sliding Window, Summary, RAG-Style, ManiGit)
- Context token budgets (128, 256, 512, 1024, 2048)
- Benchmark scenarios (Stable facts, Superseding, Constraints, Decisions, Distractors, Duplicates, Scaled length)
- Optional ablation modes
"""

from dataclasses import dataclass, field
import datetime
import random
import time
from typing import Any, Dict, List, Optional
import uuid

from manigit.evaluation.baselines import (
    BaseEvaluationMethod,
    FullHistoryBaseline,
    ManiGitEvaluationMethod,
    RAGStyleBaseline,
    SlidingWindowBaseline,
    SummaryBaseline,
)
from manigit.evaluation.metrics import compute_metrics
from manigit.evaluation.models import (
    AblationMode,
    BaselineType,
    BenchmarkQuery,
    BenchmarkResult,
    BenchmarkScenario,
)
from manigit.evaluation.scenarios import get_standard_benchmark_suite
from manigit.evaluation.storage import BenchmarkResultStorage
from manigit.models.base import ModelAdapter
from manigit.models.mock import MockModelAdapter


@dataclass
class BenchmarkConfig:
    """Configuration parameters for a benchmark experiment execution run."""
    experiment_id: str = field(default_factory=lambda: f"exp_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    methods: List[BaselineType] = field(default_factory=lambda: [
        BaselineType.FULL_HISTORY,
        BaselineType.SLIDING_WINDOW,
        BaselineType.SUMMARY,
        BaselineType.RAG_STYLE,
        BaselineType.MANIGIT,
    ])
    budgets: List[int] = field(default_factory=lambda: [128, 256, 512, 1024, 2048])
    scenarios: Optional[List[str]] = None  # None executes all standard scenarios
    sliding_window_size: int = 10
    ablation_modes: Optional[List[AblationMode]] = None
    random_seed: int = 42
    storage_dir: str = "data/processed/benchmarks/results"


class BenchmarkRunner:
    """
    Orchestrates reproducible benchmarking across methods, scenarios, and token budgets.
    """

    def __init__(
        self,
        config: Optional[BenchmarkConfig] = None,
        model: Optional[ModelAdapter] = None,
        storage: Optional[BenchmarkResultStorage] = None,
    ):
        self.config = config or BenchmarkConfig()
        self.storage = storage or BenchmarkResultStorage(base_dir=self.config.storage_dir)
        self.model = model or self._create_deterministic_eval_model()
        random.seed(self.config.random_seed)

    def _create_deterministic_eval_model(self) -> MockModelAdapter:
        """
        Creates a deterministic evaluation adapter that answers queries based
        solely on the information present in the compiled context.
        """
        def generate_handler(prompt: str) -> str:
            # Extract [Retrieved Context] and [Query] from prompt
            ctx_start = prompt.find("[Retrieved Context]")
            query_start = prompt.find("[Query]")
            
            context_block = ""
            if ctx_start != -1:
                ctx_end = query_start if query_start != -1 else len(prompt)
                context_block = prompt[ctx_start:ctx_end].lower()

            query_block = prompt[query_start:].lower() if query_start != -1 else prompt.lower()

            # Factual extraction logic for deterministic benchmark scenarios
            # Stable / Superseding database
            if "database" in query_block:
                if "before" in query_block or "prior" in query_block:
                    if "postgresql" in context_block:
                        return "Before the migration, the database was PostgreSQL."
                # If there's an unresolved active contradiction (both postgresql and mongodb present in active memory context without supersession/migrated markers)
                if "postgresql" in context_block and "mongodb" in context_block:
                    supersession_markers = ["superseded", "tombstone", "migrated", "now", "archived", "v2"]
                    if not any(m in context_block for m in supersession_markers):
                        return "Unresolved contradiction: Context contains conflicting active database specifications."
                if "mongodb" in context_block:
                    return "The current database is MongoDB."
                if "postgresql" in context_block:
                    return "The database is PostgreSQL."

            # Constraints
            if "timeout" in query_block:
                if "500 ms" in context_block or "500ms" in context_block:
                    return "The API timeout constraint is 500 ms."

            if "pool size" in query_block or "worker" in query_block:
                if "16 workers" in context_block or "16" in context_block:
                    return "The worker pool size is limited to 16 workers."

            # Decisions
            if "authentication" in query_block or "auth" in query_block:
                if "jwt" in context_block:
                    return "We decided on JWT authentication rather than cookies."

            if "billing" in query_block:
                if "event sourcing" in context_block:
                    return "We decided to adopt event sourcing for billing."

            # Technical facts
            if "configuration file" in query_block or "runtime.conf" in query_block:
                if "/etc/manigit/runtime.conf" in context_block:
                    return "The configuration file is located at /etc/manigit/runtime.conf."

            if "error code" in query_block or "socket" in query_block:
                if "err_socket_timeout_902" in context_block:
                    return "The error code is ERR_SOCKET_TIMEOUT_902."

            if "telemetry" in query_block or "metrics" in query_block:
                if "/api/v2/telemetry/events" in context_block:
                    return "The telemetry endpoint is /api/v2/telemetry/events."

            # Distractors
            if "caching service" in query_block or "port" in query_block:
                if "6379" in context_block:
                    return "The internal caching service port is 6379."

            if "deployment target" in query_block or "cluster" in query_block:
                if "us-central1-k8s-prod" in context_block:
                    return "The target cluster is us-central1-k8s-prod."

            # Duplicates
            if "retention window" in query_block:
                if "90 days" in context_block:
                    return "The retention window is 90 days."

            # Scaled Long
            if "region" in query_block:
                if "eu-west-1" in context_block:
                    return "The infrastructure is hosted in AWS region eu-west-1."

            if "kms" in query_block or "encryption" in query_block:
                if "kms-key-alpha-77" in context_block:
                    return "The encryption key identifier is KMS-KEY-ALPHA-77."

            if "freeze" in query_block:
                if "2026-12-15" in context_block:
                    return "The production deployment freeze starts on 2026-12-15."

            # Controlled Ablation Scenarios
            if "scale" in query_block or "user scale" in query_block:
                if "10k" in context_block or "10,000" in context_block:
                    return "The customer mentioned a scale of 10k users."

            if "proxy" in query_block or "egress" in query_block:
                if "proxy-gw-01" in context_block:
                    return "All egress traffic must route through proxy-gw-01."

            return "Unable to answer: fact is not present in the provided context."

        return MockModelAdapter(generate_handler=generate_handler)

    def _instantiate_method(
        self,
        method_type: BaselineType,
        ablation_mode: Optional[AblationMode] = None,
    ) -> BaseEvaluationMethod:
        """Instantiates the appropriate evaluation method class."""
        if method_type == BaselineType.FULL_HISTORY:
            return FullHistoryBaseline()
        elif method_type == BaselineType.SLIDING_WINDOW:
            return SlidingWindowBaseline(window_size=self.config.sliding_window_size)
        elif method_type == BaselineType.SUMMARY:
            return SummaryBaseline()
        elif method_type == BaselineType.RAG_STYLE:
            return RAGStyleBaseline()
        elif method_type == BaselineType.MANIGIT:
            return ManiGitEvaluationMethod(ablation_mode=ablation_mode or AblationMode.FULL)
        else:
            raise ValueError(f"Unknown baseline method: {method_type}")

    def run_benchmark(
        self,
        suite: Optional[Dict[str, BenchmarkScenario]] = None,
        save_results: bool = True,
    ) -> List[BenchmarkResult]:
        """
        Executes the configured benchmark matrix and returns all resulting trials.
        """
        all_scenarios = suite or get_standard_benchmark_suite()
        target_keys = self.config.scenarios or list(all_scenarios.keys())

        results: List[BenchmarkResult] = []

        # Build list of (method_type, ablation_mode) to evaluate
        method_variants: List[Tuple[BaselineType, Optional[AblationMode]]] = []
        for m in self.config.methods:
            if m == BaselineType.MANIGIT and self.config.ablation_modes:
                for ab in self.config.ablation_modes:
                    method_variants.append((m, ab))
            else:
                method_variants.append((m, None))

        for sc_key in target_keys:
            if sc_key not in all_scenarios:
                continue
            scenario = all_scenarios[sc_key]

            for method_type, ablation_mode in method_variants:
                method = self._instantiate_method(method_type, ablation_mode)
                method.setup(scenario, self.model)

                for budget in self.config.budgets:
                    for query in scenario.queries:
                        ans, ctx, retrieved_indices, lat_ctx, lat_gen = method.execute_query(
                            query=query,
                            budget=budget,
                            model=self.model,
                        )

                        # Check for superseded fact if applicable
                        superseded_fact = None
                        if scenario.category.value == "superseding_facts":
                            if query.is_historical:
                                superseded_fact = "MongoDB"
                            else:
                                superseded_fact = "PostgreSQL"

                        metrics = compute_metrics(
                            context_str=ctx,
                            query_str=query.query,
                            actual_answer=ans,
                            expected_answer=query.expected_answer,
                            acceptable_alternatives=query.acceptable_alternatives,
                            retrieved_indices=retrieved_indices,
                            relevant_indices=query.relevant_turn_indices,
                            budget=budget,
                            latency_context_ms=lat_ctx,
                            latency_generation_ms=lat_gen,
                            is_historical=query.is_historical,
                            superseded_fact=superseded_fact,
                        )

                        trial_result = BenchmarkResult(
                            experiment_id=self.config.experiment_id,
                            scenario_id=scenario.scenario_id,
                            method=method.name,
                            ablation_mode=ablation_mode.value if ablation_mode else None,
                            conversation_length=len(scenario.turns),
                            budget=budget,
                            query_id=query.query_id,
                            query=query.query,
                            expected_answer=query.expected_answer,
                            actual_answer=ans,
                            compiled_context=ctx,
                            metrics=metrics,
                            success=metrics.fact_recall and metrics.answer_correctness,
                            config_metadata={
                                "random_seed": self.config.random_seed,
                                "is_historical": query.is_historical,
                                "target_fact_key": query.target_fact_key,
                            },
                            retrieved_indices=retrieved_indices,
                        )
                        results.append(trial_result)

        if save_results and results:
            self.storage.save_run(self.config.experiment_id, results)

        return results
