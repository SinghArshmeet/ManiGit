"""
Required End-to-End Scenario Test for Phase 4 (Section 22):

Demonstrating multi-turn agent interaction, memory ingestion, context retrieval,
contradiction supersession, and historical memory state reconstruction:

TURN 1:
User: "We are building ManiGit. The backend database is PostgreSQL."

TURN 2:
User: "What database are we using?"
Expected: Context compiler retrieves PostgreSQL; model prompt contains PostgreSQL.

TURN 3:
User: "We have decided to migrate the backend to MongoDB."
Expected: Memory system detects contradiction/supersession; MongoDB becomes active.

TURN 4:
User: "What database are we using now?"
Expected: Current context prioritizes MongoDB.
Historical checkout before Turn 3 reconstructs PostgreSQL intact.
"""

import os
import tempfile
import unittest

from manigit.agent.models import AgentConfig
from manigit.agent.runtime import AgentRuntime
from manigit.core.models import MessageRole
from manigit.core.repository import ManiGitRepository
from manigit.models.mock import MockModelAdapter


class TestEndToEndScenario(unittest.TestCase):
    """End-to-end integration scenario verifying current knowledge vs historical knowledge."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "scenario_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        # Dynamic mock model that incorporates active context into its answer
        def dynamic_generator(prompt: str) -> str:
            if "MongoDB" in prompt:
                return "Based on active memory, our database is MongoDB."
            elif "PostgreSQL" in prompt:
                return "Based on active memory, our database is PostgreSQL."
            return "No database information found in context."

        self.mock_model = MockModelAdapter(generate_handler=dynamic_generator)
        self.runtime = AgentRuntime(
            repository=self.repo,
            model=self.mock_model,
            config=AgentConfig(default_token_budget=2048),
        )

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_complete_four_turn_scenario(self):
        """
        Execute the exact required 4-turn integration scenario.
        """
        # ======================================================================
        # TURN 1: State ingestion
        # User: "We are building ManiGit. The backend database is PostgreSQL."
        # ======================================================================
        r1 = self.runtime.run("We are building ManiGit. The backend database is PostgreSQL.")
        commit_turn1 = r1.commit_id

        self.assertIsNotNone(r1.memory_result)
        self.assertIsNotNone(r1.memory_result.new_memory)
        self.assertIn("PostgreSQL", r1.memory_result.new_memory.content)
        self.assertIsNotNone(commit_turn1)

        # Active state at commit_turn1
        state_t1 = self.runtime.reconstruct_state(commit_id=commit_turn1)
        self.assertEqual(len(state_t1), 1)
        self.assertIn("PostgreSQL", state_t1[0].content)

        # ======================================================================
        # TURN 2: Retrieval & Model Prompt Context
        # User: "What database are we using?"
        # ======================================================================
        r2 = self.runtime.run("What database are we using?")

        # 1. Context compiler should have retrieved the PostgreSQL memory
        selected_memories_t2 = r2.context_result.selected_memories
        self.assertGreater(len(selected_memories_t2), 0)
        self.assertTrue(any("PostgreSQL" in m.content for m in selected_memories_t2))

        # 2. Model adapter should have received prompt containing PostgreSQL memory
        generate_calls = [c for c in self.mock_model.call_history if c["method"] == "generate"]
        prompt_t2 = generate_calls[-1]["prompt"]
        self.assertIn("[Active Memory Context]", prompt_t2)
        self.assertIn("PostgreSQL", prompt_t2)

        # 3. Model generated answer based on context
        self.assertIn("PostgreSQL", r2.content)

        # Turn 2 commit should be unchanged from Turn 1 (no redundant commit for query)
        self.assertEqual(r2.commit_id, commit_turn1)

        # ======================================================================
        # TURN 3: Contradiction & Migration
        # User: "We have decided to migrate the backend to MongoDB."
        # ======================================================================
        r3 = self.runtime.run("We have decided to migrate the backend to MongoDB.")
        commit_turn3 = r3.commit_id

        self.assertNotEqual(commit_turn3, commit_turn1)
        self.assertIsNotNone(r3.memory_result)
        self.assertTrue(r3.memory_result.contradiction.has_contradiction)
        self.assertEqual(r3.memory_result.superseded_memory_id, state_t1[0].id)
        self.assertIn("MongoDB", r3.memory_result.new_memory.content)

        # Active state at commit_turn3 now only contains MongoDB
        state_t3 = self.runtime.reconstruct_state(commit_id=commit_turn3)
        self.assertEqual(len(state_t3), 1)
        self.assertIn("MongoDB", state_t3[0].content)

        # ======================================================================
        # TURN 4: Updated Context & Historical Audit
        # User: "What database are we using now?"
        # ======================================================================
        r4 = self.runtime.run("What database are we using now?")

        # 1. Current context should prioritize MongoDB
        selected_memories_t4 = r4.context_result.selected_memories
        self.assertEqual(len(selected_memories_t4), 1)
        self.assertIn("MongoDB", selected_memories_t4[0].content)
        self.assertNotIn("PostgreSQL", selected_memories_t4[0].content)

        # 2. Model generated answer reflects current active knowledge
        self.assertIn("MongoDB", r4.content)

        # ======================================================================
        # HISTORICAL VERIFICATION: Current Knowledge vs Historical Knowledge
        # ======================================================================
        # Compile context at historical commit_turn1
        historical_context = self.runtime.compile_context(
            query="What database are we using?",
            commit_id=commit_turn1,
        )
        self.assertEqual(len(historical_context.selected_memories), 1)
        self.assertIn("PostgreSQL", historical_context.selected_memories[0].content)
        self.assertNotIn("MongoDB", historical_context.selected_memories[0].content)

        # Reconstruct memory state at historical commit_turn1
        reconstructed_historical_state = self.runtime.reconstruct_state(commit_id=commit_turn1)
        self.assertEqual(len(reconstructed_historical_state), 1)
        self.assertIn("PostgreSQL", reconstructed_historical_state[0].content)

        # Reconstruct memory state at current HEAD (commit_turn3)
        reconstructed_current_state = self.runtime.reconstruct_state(commit_id=commit_turn3)
        self.assertEqual(len(reconstructed_current_state), 1)
        self.assertIn("MongoDB", reconstructed_current_state[0].content)

        # Verify all raw messages are preserved in immutable archive
        messages = self.runtime.get_history()
        self.assertEqual(len(messages), 8)  # 4 user messages + 4 assistant responses
        self.assertEqual(messages[0].role, MessageRole.USER.value)
        self.assertIn("PostgreSQL", messages[0].content)
        self.assertEqual(messages[4].role, MessageRole.USER.value)
        self.assertIn("MongoDB", messages[4].content)


if __name__ == "__main__":
    unittest.main()
