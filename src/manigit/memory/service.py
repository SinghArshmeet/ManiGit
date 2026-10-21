"""
Service-level workflow for memory evaluation, classification, contradiction resolution,
and preparation of versioned commit states.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from manigit.core.models import Commit, Memory, MemoryStatus, MemoryTier, Message
from manigit.core.repository import ManiGitRepository
from manigit.memory.classifier import ClassificationResult, MemoryClassifier
from manigit.memory.contradiction import ContradictionDetector, ContradictionResult
from manigit.memory.judge import MemoryJudge
from manigit.memory.rules import RuleEngine
from manigit.memory.summarizer import MemorySummarizer
from manigit.memory.why import WhyReport
from manigit.models.base import ModelAdapter


@dataclass(frozen=True)
class MemoryProcessingResult:
    """The structured result of processing an incoming message through memory intelligence."""
    classification: ClassificationResult
    contradiction: ContradictionResult
    why_report: WhyReport
    new_memory: Optional[Memory]
    superseded_memory_id: Optional[str]
    active_memory_ids_for_commit: List[str]


class MemoryService:
    """
    Coordinates the Phase 2 Memory Intelligence pipeline:
    Message -> Rule Analysis -> LLM Judge -> Classification -> Contradiction Check -> Why Report -> Commit Staging.
    """

    def __init__(
        self,
        repo: ManiGitRepository,
        model_adapter: ModelAdapter,
        rule_engine: Optional[RuleEngine] = None,
        judge: Optional[MemoryJudge] = None,
        contradiction_detector: Optional[ContradictionDetector] = None,
        summarizer: Optional[MemorySummarizer] = None,
    ):
        self.repo = repo
        self.model_adapter = model_adapter
        self.rule_engine = rule_engine or RuleEngine()
        self.judge = judge or MemoryJudge(model_adapter)
        self.classifier = MemoryClassifier(self.rule_engine, self.judge)
        self.contradiction_detector = contradiction_detector or ContradictionDetector()
        self.summarizer = summarizer or MemorySummarizer(model_adapter)

    def process_message(
        self,
        message: Message,
        branch_name: Optional[str] = None,
    ) -> MemoryProcessingResult:
        """
        Evaluate an ingested message against the current active memory state.
        
        Determines tier, detects contradictions, creates memory records with provenance,
        generates a Why Report, and computes the new candidate active memory IDs.
        """
        target_branch = branch_name or self.repo.active_branch
        head_commit = self.repo.get_current_head(target_branch)

        # 1. Reconstruct current active memory state
        active_memories: List[Memory] = []
        if head_commit:
            active_memories = self.repo.reconstruct_memory_state(head_commit.id)

        # 2. Classify message into VERBATIM, SUMMARY, or ARCHIVED
        classification = self.classifier.classify(
            content=message.content,
            source_message_ids=[message.id],
            active_memories=active_memories,
        )

        # 3. Contradiction & supersession check
        contradiction = self.contradiction_detector.detect(
            new_text=message.content,
            active_memories=active_memories,
        )

        # 4. Resolve state updates and active memory list
        active_ids = [m.id for m in active_memories]
        new_memory: Optional[Memory] = None
        superseded_id: Optional[str] = None

        if contradiction.has_contradiction and contradiction.superseded_memory_id:
            superseded_id = contradiction.superseded_memory_id
            if superseded_id in active_ids:
                active_ids.remove(superseded_id)

        tokens_before = sum(m.token_count for m in active_memories)

        if classification.tier in (MemoryTier.VERBATIM.value, MemoryTier.SUMMARY.value):
            # Create new persistent memory record linked to message
            new_memory = self.repo.create_memory(
                content=classification.content_to_store,
                tier=classification.tier,
                source_message_ids=[message.id],
                confidence=classification.confidence,
                status=MemoryStatus.ACTIVE,
                metadata={
                    "matched_rules": classification.matched_rules,
                    "supersedes": superseded_id,
                },
            )
            active_ids.append(new_memory.id)

        # Calculate tokens after staging
        tokens_after = tokens_before
        if new_memory:
            tokens_after += new_memory.token_count
        if superseded_id:
            for m in active_memories:
                if m.id == superseded_id:
                    tokens_after -= m.token_count

        # 5. Build structured Why Report
        decision = classification.decision
        if contradiction.has_contradiction:
            decision = "SUPERSEDE"

        why_report = WhyReport(
            decision=decision,
            tier=classification.tier,
            confidence=classification.confidence,
            reason=contradiction.explanation if contradiction.has_contradiction else classification.reason,
            source_message_ids=[message.id],
            matched_rules=classification.matched_rules,
            predecessor_memory_id=superseded_id,
            contradiction_info={
                "conflict_type": contradiction.conflict_type,
                "historical_fact": contradiction.historical_fact,
                "current_fact": contradiction.current_fact,
            } if contradiction.has_contradiction else None,
            tokens_before=tokens_before,
            tokens_after=max(0, tokens_after),
        )

        return MemoryProcessingResult(
            classification=classification,
            contradiction=contradiction,
            why_report=why_report,
            new_memory=new_memory,
            superseded_memory_id=superseded_id,
            active_memory_ids_for_commit=active_ids,
        )

    def commit_memory_update(
        self,
        result: MemoryProcessingResult,
        commit_message: str,
        branch_name: Optional[str] = None,
        author: str = "agent:auto",
    ) -> Commit:
        """
        Persist the staged memory state as an immutable commit with full Why Report metadata.
        """
        return self.repo.create_commit(
            message=commit_message,
            reason=result.why_report.reason,
            active_memory_ids=result.active_memory_ids_for_commit,
            branch_name=branch_name or self.repo.active_branch,
            author=author,
            metadata={"why_report": result.why_report.to_dict()},
        )
