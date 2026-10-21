"""
Evaluation baseline implementations for comparative research benchmarking.

Provides five uniform memory/context strategies:
1. FULL_HISTORY: Unbounded / budget-truncated chronological message concatenation.
2. SLIDING_WINDOW: Most recent N messages within budget.
3. SUMMARY: Running condensation of conversational history within budget.
4. RAG_STYLE: Deterministic lexical retrieval over raw message history.
5. MANIGIT: Transparent, versioned, provenance-aware memory selection.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from manigit.agent.runtime import AgentRuntime
from manigit.context.compiler import ContextCompiler
from manigit.context.models import ContextResult, ScoringWeights
from manigit.context.scoring import ScoringEngine
from manigit.core.models import MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository
from manigit.core.tokens import estimate_tokens
from manigit.evaluation.models import (
    AblationMode,
    BaselineType,
    BenchmarkQuery,
    BenchmarkScenario,
    ScenarioTurn,
)
from manigit.memory.classifier import MemoryClassifier
from manigit.memory.contradiction import ContradictionDetector, ContradictionResult
from manigit.memory.service import MemoryService
from manigit.models.base import ModelAdapter


class DisabledContradictionDetector(ContradictionDetector):
    """
    Ablation variant: Contradiction and supersession detection is disabled.
    Does not detect conflicts or supersede active memories.
    """

    def detect(self, new_text: str, active_memories: List[Any]) -> ContradictionResult:
        return ContradictionResult(
            has_contradiction=False,
            conflict_type="NONE",
            explanation="Contradiction detection disabled by ablation.",
        )


class NoConfidenceMemoryClassifier(MemoryClassifier):
    """
    Ablation variant: Confidence-aware classification is neutralized.
    Confidence values are retained as metadata but ignored by the decision path.
    Specifically, low-confidence archive candidates are NOT escalated to VERBATIM.
    """

    ARCHIVE_CONFIDENCE_THRESHOLD = 0.0


class BaseEvaluationMethod(ABC):
    """Abstract interface for benchmarked context/memory strategies."""

    def __init__(self, name: str, baseline_type: BaselineType):
        self.name = name
        self.baseline_type = baseline_type
        self.scenario: Optional[BenchmarkScenario] = None

    @abstractmethod
    def setup(self, scenario: BenchmarkScenario, model: ModelAdapter) -> None:
        """Initialize the method with the conversation scenario."""
        pass

    @abstractmethod
    def compile_context(
        self,
        query: BenchmarkQuery,
        budget: int,
    ) -> Tuple[str, List[int]]:
        """
        Compile context for a query under token budget.
        Returns:
            Tuple[context_str, retrieved_turn_indices]
        """
        pass

    def execute_query(
        self,
        query: BenchmarkQuery,
        budget: int,
        model: ModelAdapter,
    ) -> Tuple[str, str, List[int], float, float]:
        """
        Executes query, measuring retrieval and generation latencies.
        Returns:
            Tuple[actual_answer, compiled_context, retrieved_indices, latency_ctx_ms, latency_gen_ms]
        """
        t0 = time.perf_counter()
        compiled_context, retrieved_indices = self.compile_context(query, budget)
        t1 = time.perf_counter()
        latency_ctx_ms = (t1 - t0) * 1000.0

        # Construct unified prompt
        prompt_parts: List[str] = []
        if compiled_context.strip():
            prompt_parts.append(f"[Retrieved Context]\n{compiled_context.strip()}")
        prompt_parts.append(f"[Query]\n{query.query.strip()}")
        full_prompt = "\n\n".join(prompt_parts)

        t2 = time.perf_counter()
        answer = model.generate(full_prompt)
        t3 = time.perf_counter()
        latency_gen_ms = (t3 - t2) * 1000.0

        return answer, compiled_context, retrieved_indices, latency_ctx_ms, latency_gen_ms


class FullHistoryBaseline(BaseEvaluationMethod):
    """
    Baseline 1: Chronological naive message accumulation.
    Packs conversation history from turn 0 onward until token budget is exhausted.
    """

    def __init__(self):
        super().__init__("Full History", BaselineType.FULL_HISTORY)
        self.turns: List[ScenarioTurn] = []

    def setup(self, scenario: BenchmarkScenario, model: ModelAdapter) -> None:
        self.scenario = scenario
        self.turns = list(scenario.turns)

    def compile_context(
        self,
        query: BenchmarkQuery,
        budget: int,
    ) -> Tuple[str, List[int]]:
        included_lines: List[str] = []
        included_indices: List[int] = []

        for turn in self.turns:
            line = f"Turn {turn.turn_index} [{turn.role}]: {turn.content}"
            if estimate_tokens("\n".join(included_lines + [line])) <= budget:
                included_lines.append(line)
                included_indices.append(turn.turn_index)
            else:
                break

        context_str = "\n".join(included_lines)
        return context_str, included_indices


class SlidingWindowBaseline(BaseEvaluationMethod):
    """
    Baseline 2: Sliding Window.
    Retains only the most recent N turns, packed within token budget.
    """

    def __init__(self, window_size: int = 10):
        super().__init__(f"Sliding Window (N={window_size})", BaselineType.SLIDING_WINDOW)
        self.window_size = window_size
        self.turns: List[ScenarioTurn] = []

    def setup(self, scenario: BenchmarkScenario, model: ModelAdapter) -> None:
        self.scenario = scenario
        self.turns = list(scenario.turns)

    def compile_context(
        self,
        query: BenchmarkQuery,
        budget: int,
    ) -> Tuple[str, List[int]]:
        # Take at most window_size most recent turns
        recent_turns = self.turns[-self.window_size:] if self.turns else []
        
        # Pack from most recent backwards or chronological within window
        included_lines: List[str] = []
        included_indices: List[int] = []
        # We keep chronological order among the window
        for turn in recent_turns:
            line = f"Turn {turn.turn_index} [{turn.role}]: {turn.content}"
            if estimate_tokens("\n".join(included_lines + [line])) <= budget:
                included_lines.append(line)
                included_indices.append(turn.turn_index)

        context_str = "\n".join(included_lines)
        return context_str, included_indices


class SummaryBaseline(BaseEvaluationMethod):
    """
    Baseline 3: Running Summary.
    Maintains a condensed running summary of prior dialogue turns within budget.
    """

    def __init__(self):
        super().__init__("Running Summary", BaselineType.SUMMARY)
        self.turns: List[ScenarioTurn] = []
        self.summary_text: str = ""

    def setup(self, scenario: BenchmarkScenario, model: ModelAdapter) -> None:
        self.scenario = scenario
        self.turns = list(scenario.turns)

        # Build running summary deterministically
        # Extract meaningful factual statements from user turns
        summary_points: List[str] = []
        for turn in self.turns:
            if turn.contains_fact:
                summary_points.append(f"- Fact: {turn.contains_fact}")
            elif not turn.is_distractor and turn.role == "user":
                summary_points.append(f"- Note: {turn.content}")

        if summary_points:
            self.summary_text = "Running Dialogue Summary:\n" + "\n".join(summary_points)
        else:
            self.summary_text = "Running Dialogue Summary:\n- General discussion with no explicit constraints."

    def compile_context(
        self,
        query: BenchmarkQuery,
        budget: int,
    ) -> Tuple[str, List[int]]:
        tokens = estimate_tokens(self.summary_text)
        if tokens <= budget:
            return self.summary_text, [t.turn_index for t in self.turns if t.contains_fact]
        
        # Truncate summary if exceeding budget
        lines = self.summary_text.splitlines()
        packed_lines: List[str] = []
        for l in lines:
            if estimate_tokens("\n".join(packed_lines + [l])) <= budget:
                packed_lines.append(l)
            else:
                break
        return "\n".join(packed_lines), [t.turn_index for t in self.turns if t.contains_fact]


class RAGStyleBaseline(BaseEvaluationMethod):
    """
    Baseline 4: Lexical RAG over raw conversation messages.
    Performs deterministic term-frequency lexical retrieval over raw turns.
    """

    def __init__(self):
        super().__init__("RAG-Style (Raw Messages)", BaselineType.RAG_STYLE)
        self.turns: List[ScenarioTurn] = []

    def setup(self, scenario: BenchmarkScenario, model: ModelAdapter) -> None:
        self.scenario = scenario
        self.turns = list(scenario.turns)

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
        return {w for w in cleaned.split() if len(w) > 1}

    def compile_context(
        self,
        query: BenchmarkQuery,
        budget: int,
    ) -> Tuple[str, List[int]]:
        q_tokens = self._tokenize(query.query)
        scored_turns: List[Tuple[float, int, ScenarioTurn]] = []

        for turn in self.turns:
            t_tokens = self._tokenize(turn.content)
            if not t_tokens or not q_tokens:
                score = 0.0
            else:
                intersection = q_tokens.intersection(t_tokens)
                # Jaccard overlap score
                union = q_tokens.union(t_tokens)
                score = len(intersection) / len(union) if union else 0.0
            
            # Recency tie-breaker
            scored_turns.append((score, turn.turn_index, turn))

        # Sort descending by score, then by turn_index
        scored_turns.sort(key=lambda x: (x[0], x[1]), reverse=True)

        included_turns: List[ScenarioTurn] = []

        for score, idx, turn in scored_turns:
            if score <= 0.0 and len(included_turns) > 0:
                # Do not pack completely irrelevant turns if we already have matches
                continue
            test_turns = sorted(included_turns + [turn], key=lambda t: t.turn_index)
            test_lines = [f"Turn {t.turn_index} [{t.role}]: {t.content}" for t in test_turns]
            if estimate_tokens("\n".join(test_lines)) <= budget:
                included_turns.append(turn)

        # Re-sort chronologically for prompt readability
        included_turns.sort(key=lambda t: t.turn_index)
        lines = [f"Turn {t.turn_index} [{t.role}]: {t.content}" for t in included_turns]
        indices = [t.turn_index for t in included_turns]
        return "\n".join(lines), indices


class ManiGitEvaluationMethod(BaseEvaluationMethod):
    """
    Baseline 5: ManiGit Versioned Memory.
    Uses ManiGit Repository + MemoryService + ContextCompiler + AgentRuntime.
    Provides transparent, versioned, budget-constrained memory context.
    """

    def __init__(self, ablation_mode: AblationMode = AblationMode.FULL):
        super().__init__(f"ManiGit ({ablation_mode.value})", BaselineType.MANIGIT)
        self.ablation_mode = ablation_mode
        self.repository: Optional[ManiGitRepository] = None
        self.runtime: Optional[AgentRuntime] = None
        self.compiler: Optional[ContextCompiler] = None
        self.turn_commit_map: Dict[int, str] = {}
        self.first_fact_commit_id: Optional[str] = None

    def setup(self, scenario: BenchmarkScenario, model: ModelAdapter) -> None:
        self.scenario = scenario
        # In-memory clean repository
        self.repository = ManiGitRepository(db_path=":memory:")
        self.repository.initialize_repository()
        # Select contradiction detector based on ablation mode
        if self.ablation_mode == AblationMode.NO_CONTRADICTION:
            detector = DisabledContradictionDetector()
        else:
            detector = ContradictionDetector()

        mem_service = MemoryService(self.repository, model, contradiction_detector=detector)

        # Neutralize confidence in classifier if NO_CONFIDENCE ablation
        if self.ablation_mode == AblationMode.NO_CONFIDENCE:
            mem_service.classifier = NoConfidenceMemoryClassifier(
                mem_service.rule_engine,
                mem_service.judge,
            )

        # Configure custom weights for ablation
        if self.ablation_mode == AblationMode.NO_TIER:
            weights = ScoringWeights(
                verbatim_boost=0.0,
                summary_boost=0.0,
            )
        elif self.ablation_mode == AblationMode.NO_CONFIDENCE:
            weights = ScoringWeights(
                confidence_weight=0.0,
            )
        elif self.ablation_mode == AblationMode.RETRIEVAL_ONLY:
            weights = ScoringWeights(
                relevance_weight=1.0,
                constraint_boost=0.0,
                decision_boost=0.0,
                verbatim_boost=0.0,
                summary_boost=0.0,
                confidence_weight=0.0,
                recency_weight=0.0,
            )
        elif self.ablation_mode == AblationMode.RETRIEVAL_TIERING:
            weights = ScoringWeights(
                relevance_weight=0.6,
                constraint_boost=0.2,
                decision_boost=0.1,
                verbatim_boost=0.1,
                summary_boost=0.0,
                confidence_weight=0.0,
                recency_weight=0.0,
            )
        elif self.ablation_mode == AblationMode.RETRIEVAL_TIERING_CONFIDENCE:
            weights = ScoringWeights(
                relevance_weight=0.5,
                constraint_boost=0.15,
                decision_boost=0.1,
                verbatim_boost=0.1,
                summary_boost=0.05,
                confidence_weight=0.1,
                recency_weight=0.0,
            )
        else:  # FULL or NO_CONTRADICTION
            weights = ScoringWeights()

        scoring_engine = ScoringEngine(weights=weights)
        self.compiler = ContextCompiler(self.repository, scoring_engine=scoring_engine)
        self.runtime = AgentRuntime(
            repository=self.repository,
            model=model,
            memory_service=mem_service,
            context_compiler=self.compiler,
        )

        # Feed scenario turns through AgentRuntime
        for turn in scenario.turns:
            if turn.role == "user":
                response = self.runtime.run(
                    user_message=turn.content,
                    session_id="benchmark_session",
                )
                commit_id = response.turn.commit_id
                self.turn_commit_map[turn.turn_index] = commit_id

                # Save early commit milestone for historical query verification
                if turn.contains_fact and self.first_fact_commit_id is None:
                    self.first_fact_commit_id = commit_id

    def compile_context(
        self,
        query: BenchmarkQuery,
        budget: int,
    ) -> Tuple[str, List[int]]:
        if not self.runtime or not self.compiler:
            return "", []

        # Target historical commit if querying superseded state
        target_commit = None
        if query.is_historical and self.first_fact_commit_id:
            target_commit = self.first_fact_commit_id

        context_result = self.runtime.compile_context(
            query=query.query,
            token_budget=budget,
            commit_id=target_commit,
        )

        context_str = context_result.to_prompt_context()

        # Find which turns contributed to the included memories
        included_turn_indices: List[int] = []
        for mem in context_result.selected_memories:
            if mem.content.strip() and mem.content.strip().lower() in context_str.lower():
                for turn in (self.scenario.turns if self.scenario else []):
                    if turn.contains_fact and turn.contains_fact.lower() in mem.content.lower():
                        if turn.turn_index not in included_turn_indices:
                            included_turn_indices.append(turn.turn_index)
                    elif turn.content.strip().lower() in mem.content.lower():
                        if turn.turn_index not in included_turn_indices:
                            included_turn_indices.append(turn.turn_index)

        return context_str, included_turn_indices
