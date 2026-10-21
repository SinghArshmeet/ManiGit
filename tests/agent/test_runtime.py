"""
Unit and integration tests for ManiGit AgentRuntime.
"""

import os
import tempfile
import unittest

from manigit.agent.exceptions import (
    EmptyMessageError,
    InvalidBranchError,
    ModelAdapterError,
)
from manigit.agent.models import AgentConfig
from manigit.agent.runtime import AgentRuntime
from manigit.core.models import MemoryStatus, MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository
from manigit.models.mock import MockModelAdapter


class TestAgentRuntime(unittest.TestCase):
    """Test suite for AgentRuntime orchestration across all multi-turn lifecycle steps."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "agent_runtime_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        self.mock_model = MockModelAdapter()
        self.runtime = AgentRuntime(
            repository=self.repo,
            model=self.mock_model,
            config=AgentConfig(default_token_budget=1024),
        )

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_basic_agent_turn(self):
        """
        Verify the basic turn lifecycle:
        1. User message stored in database.
        2. Context compiled.
        3. Model adapter invoked.
        4. Assistant response stored in database.
        5. AgentResponse returned with auditable turn details.
        """
        response = self.runtime.run("Hello, this is a test greeting!")

        self.assertEqual(response.content, "Mock response for prompt.")
        self.assertEqual(response.turn.user_message, "Hello, this is a test greeting!")
        self.assertEqual(response.turn.assistant_response, "Mock response for prompt.")

        # Verify raw user message in database
        user_msg = self.repo.get_message(response.user_message_id)
        self.assertEqual(user_msg.content, "Hello, this is a test greeting!")
        self.assertEqual(user_msg.role, MessageRole.USER.value)

        # Verify raw assistant message in database
        asst_msg = self.repo.get_message(response.assistant_message_id)
        self.assertEqual(asst_msg.content, "Mock response for prompt.")
        self.assertEqual(asst_msg.role, MessageRole.ASSISTANT.value)

        # Verify model was called with constructed prompt
        generate_calls = [c for c in self.mock_model.call_history if c["method"] == "generate"]
        self.assertEqual(len(generate_calls), 1)
        self.assertIn("[User Message]\nHello, this is a test greeting!", generate_calls[0]["prompt"])

    def test_context_integration_and_budget_enforcement(self):
        """
        Verify that ContextCompiler is used and token budgets are strictly enforced.
        """
        # Pre-seed an active memory
        m_seed = self.repo.append_message("s1", MessageRole.USER, "Constraint: Max batch size is 32.")
        mem_seed = self.repo.create_memory("Batch size = 32", MemoryTier.VERBATIM, [m_seed.id])
        self.repo.create_commit("Seed memory", "Setup", [mem_seed.id])

        # Query relevant to batch size
        response = self.runtime.run("What is the configured batch size?", token_budget=500)

        # Context compiler should have selected mem_seed
        self.assertGreater(len(response.context_result.selected_memories), 0)
        self.assertEqual(response.context_result.selected_memories[0].memory_id, mem_seed.id)

        # Verify model prompt contained the compiled context block
        generate_calls = [c for c in self.mock_model.call_history if c["method"] == "generate"]
        prompt_used = generate_calls[-1]["prompt"]
        self.assertIn("[Active Memory Context]", prompt_used)
        self.assertIn("Batch size = 32", prompt_used)

        # Verify token budget invariant
        self.assertLessEqual(response.token_usage.context_tokens, 500)

    def test_memory_integration_and_tiering(self):
        """
        Verify that user statements containing decisions or constraints become active memories
        with correct provenance linking to the raw message ID.
        """
        response = self.runtime.run("We decided that the primary language must be Python.")

        self.assertIsNotNone(response.memory_result)
        self.assertEqual(response.memory_result.classification.tier, MemoryTier.VERBATIM.value)
        self.assertIsNotNone(response.memory_result.new_memory)

        # Verify provenance points to the ingested user message
        new_mem = response.memory_result.new_memory
        self.assertEqual(new_mem.source_message_ids, [response.user_message_id])

        # Verify active memory in repository contains the new memory
        head_commit = self.repo.get_current_head("main")
        active_state = self.repo.reconstruct_memory_state(head_commit.id)
        self.assertIn(new_mem.id, [m.id for m in active_state])

    def test_commit_creation_and_dag_progression(self):
        """
        Verify that meaningful memory updates produce an immutable commit,
        advancing branch HEAD and recording Why Report metadata.
        """
        head_before = self.repo.get_current_head("main")

        response = self.runtime.run("Requirement: Authentication must use OAuth2.")

        head_after = self.repo.get_current_head("main")
        self.assertNotEqual(head_before.id, head_after.id)
        self.assertEqual(head_after.parent_commit_id, head_before.id)
        self.assertEqual(response.commit_id, head_after.id)

        # Verify commit contains why_report metadata
        commit_obj = self.repo.get_commit(head_after.id)
        self.assertIn("why_report", commit_obj.metadata)
        self.assertEqual(commit_obj.metadata["why_report"]["tier"], MemoryTier.VERBATIM.value)

    def test_no_redundant_commit_on_pure_query(self):
        """
        Verify that pure inquiries do not pollute the commit graph with empty commits.
        """
        # First turn: learn a fact
        self.runtime.run("Backend database is PostgreSQL.")
        head_after_turn1 = self.repo.get_current_head("main")

        # Second turn: pure query
        response2 = self.runtime.run("What database are we using?")
        head_after_turn2 = self.repo.get_current_head("main")

        # HEAD commit should NOT have changed on pure inquiry
        self.assertEqual(head_after_turn1.id, head_after_turn2.id)
        self.assertEqual(response2.commit_id, head_after_turn1.id)

    def test_historical_reconstruction_unaffected_by_new_turns(self):
        """
        Verify that older commits retain their exact historical memory state
        even after multiple subsequent turns add new memories.
        """
        # Turn 1
        r1 = self.runtime.run("Constraint: Service port is 8080.")
        commit_t1 = r1.commit_id

        # Turn 2
        r2 = self.runtime.run("Constraint: Timeout is 30 seconds.")
        commit_t2 = r2.commit_id

        # Turn 3
        r3 = self.runtime.run("Constraint: Max connections is 100.")
        commit_t3 = r3.commit_id

        # Reconstruct at commit_t1: should only have Service port
        state_t1 = self.runtime.reconstruct_state(commit_id=commit_t1)
        self.assertEqual(len(state_t1), 1)
        self.assertIn("8080", state_t1[0].content)

        # Reconstruct at commit_t3: should have all 3
        state_t3 = self.runtime.reconstruct_state(commit_id=commit_t3)
        self.assertEqual(len(state_t3), 3)

    def test_contradiction_handling_and_supersession(self):
        """
        Verify contradiction handling:
        Initial fact is superseded in active view but remains intact in historical snapshot.
        """
        # Turn 1: Initial decision
        r1 = self.runtime.run("Backend database = PostgreSQL")
        commit1 = r1.commit_id

        # Turn 2: Replacement decision
        r2 = self.runtime.run("Backend database = MongoDB")
        commit2 = r2.commit_id

        self.assertTrue(r2.memory_result.contradiction.has_contradiction)

        # Active state at commit2 has MongoDB
        state2 = self.runtime.reconstruct_state(commit_id=commit2)
        self.assertEqual(len(state2), 1)
        self.assertIn("MongoDB", state2[0].content)

        # Historical state at commit1 has PostgreSQL intact
        state1 = self.runtime.reconstruct_state(commit_id=commit1)
        self.assertEqual(len(state1), 1)
        self.assertIn("PostgreSQL", state1[0].content)

    def test_branch_isolation_and_no_silent_switch(self):
        """
        Verify agent can run on a designated branch without modifying the active branch pointer.
        """
        initial_branch = self.repo.active_branch
        self.repo.create_branch("feature-auth")

        response = self.runtime.run(
            user_message="Auth provider is Auth0.",
            branch="feature-auth",
        )

        # Active branch remained unchanged
        self.assertEqual(self.repo.active_branch, initial_branch)
        self.assertEqual(response.branch, "feature-auth")

        # feature-auth HEAD has the new memory
        head_auth = self.repo.get_current_head("feature-auth")
        auth_memories = self.runtime.reconstruct_state(branch="feature-auth")
        self.assertEqual(len(auth_memories), 1)
        self.assertIn("Auth0", auth_memories[0].content)

        # main HEAD does NOT have this memory
        main_memories = self.runtime.reconstruct_state(branch="main")
        self.assertNotIn("Auth0", [m.content for m in main_memories])

    def test_failure_model_adapter_preserves_raw_user_message(self):
        """
        Verify failure safety:
        If model generation fails, the raw user message is preserved in SQLite,
        no assistant message is stored, and no memory commit is staged.
        """
        failing_model = MockModelAdapter()
        def broken_generate(prompt):
            raise RuntimeError("API network connection failure")
        failing_model.generate_handler = broken_generate

        failing_runtime = AgentRuntime(
            repository=self.repo,
            model=failing_model,
        )

        messages_before = len(self.repo.get_messages())
        commits_before = len(self.repo.get_commit_history("main"))

        with self.assertRaises(ModelAdapterError) as ctx:
            failing_runtime.run("Critical instructions that must be recorded")

        self.assertIn("API network connection failure", str(ctx.exception))

        # Raw user message WAS preserved in database!
        messages_after = self.repo.get_messages()
        self.assertEqual(len(messages_after), messages_before + 1)
        self.assertEqual(messages_after[-1].content, "Critical instructions that must be recorded")
        self.assertEqual(messages_after[-1].role, MessageRole.USER.value)

        # No assistant message was added
        self.assertNotIn(MessageRole.ASSISTANT.value, [m.role for m in messages_after[-1:]])

        # No commit was created
        commits_after = len(self.repo.get_commit_history("main"))
        self.assertEqual(commits_before, commits_after)

    def test_failure_empty_message_raises_error(self):
        """Verify empty and whitespace inputs raise EmptyMessageError."""
        with self.assertRaises(EmptyMessageError):
            self.runtime.run("")
        with self.assertRaises(EmptyMessageError):
            self.runtime.run("   \n\t  ")

    def test_failure_invalid_branch_raises_error(self):
        """Verify targeting non-existent branch raises InvalidBranchError."""
        with self.assertRaises(InvalidBranchError):
            self.runtime.run("Hello", branch="nonexistent-branch-xyz")

    def test_zero_budget_execution(self):
        """Verify execution succeeds with token_budget=0 without exceeding budget."""
        response = self.runtime.run("Hello world", token_budget=0)
        self.assertEqual(response.token_usage.context_tokens, 0)
        self.assertEqual(len(response.context_result.selected_memories), 0)

    def test_token_accounting(self):
        """Verify comprehensive token accounting across context, input, output, and total."""
        response = self.runtime.run("Brief turn.")
        usage = response.token_usage

        self.assertGreaterEqual(usage.context_tokens, 0)
        self.assertGreater(usage.user_message_tokens, 0)
        self.assertGreater(usage.estimated_input_tokens, 0)
        self.assertGreater(usage.output_tokens, 0)
        self.assertEqual(usage.total_tokens, usage.estimated_input_tokens + usage.output_tokens)

    def test_context_compiler_remains_mutation_free(self):
        """
        Verify that compiling context via the runtime produces zero database writes.
        """
        conn = self.repo.db.connect()
        counts_before = {
            "messages": conn.execute("SELECT count(*) as c FROM messages").fetchone()["c"],
            "memories": conn.execute("SELECT count(*) as c FROM memories").fetchone()["c"],
            "commits": conn.execute("SELECT count(*) as c FROM commits").fetchone()["c"],
        }

        self.runtime.compile_context("any search query", token_budget=500)

        counts_after = {
            "messages": conn.execute("SELECT count(*) as c FROM messages").fetchone()["c"],
            "memories": conn.execute("SELECT count(*) as c FROM memories").fetchone()["c"],
            "commits": conn.execute("SELECT count(*) as c FROM commits").fetchone()["c"],
        }
        self.assertEqual(counts_before, counts_after)


if __name__ == "__main__":
    unittest.main()
