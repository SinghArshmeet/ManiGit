"""
Required Integration Test for Phase 3 (Section 15):
Demonstrating that query relevance dominates over blind memory tier prioritization.
"""

import os
import tempfile
import unittest

from manigit.context.compiler import ContextCompiler
from manigit.core.models import MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestPriorityIntegrationScenario(unittest.TestCase):
    """
    Integration scenario with the 4 required memories:
    1. Backend database is PostgreSQL.
    2. Deployment target is AWS.
    3. Project deadline is December 15.
    4. Backend database must use PostgreSQL.
    
    Verifies that:
    - Query 'What database are we using?' prioritizes PostgreSQL memories above AWS and deadline.
    - Query 'What is our deployment target?' prioritizes AWS memory above PostgreSQL and deadline.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "priority_integration.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        # Seed raw messages
        m1 = self.repo.append_message("s1", MessageRole.USER, "Backend database is PostgreSQL.")
        m2 = self.repo.append_message("s1", MessageRole.USER, "Deployment target is AWS.")
        m3 = self.repo.append_message("s1", MessageRole.USER, "Project deadline is December 15.")
        m4 = self.repo.append_message("s1", MessageRole.USER, "Backend database must use PostgreSQL.")

        # Create the 4 required memories
        # Notice: mem1 is SUMMARY, mem2 is VERBATIM, mem3 is VERBATIM, mem4 is VERBATIM
        self.mem1 = self.repo.create_memory("Backend database is PostgreSQL.", MemoryTier.SUMMARY, [m1.id])
        self.mem2 = self.repo.create_memory("Deployment target is AWS.", MemoryTier.VERBATIM, [m2.id])
        self.mem3 = self.repo.create_memory("Project deadline is December 15.", MemoryTier.VERBATIM, [m3.id])
        self.mem4 = self.repo.create_memory("Backend database must use PostgreSQL.", MemoryTier.VERBATIM, [m4.id])

        # Commit all 4 into active memory state
        self.commit = self.repo.create_commit(
            message="Initial project requirements",
            reason="Seed 4 foundational memories",
            active_memory_ids=[self.mem1.id, self.mem2.id, self.mem3.id, self.mem4.id],
        )

        self.compiler = ContextCompiler(self.repo)

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_database_query_prioritizes_postgresql_above_aws_and_deadline(self):
        """
        Query: 'What database are we using?'
        Expected: PostgreSQL-related memories must be prioritized above unrelated deployment/deadline memories.
        """
        query = "What database are we using?"
        # Token budget of 18 tokens accommodates mem4 (10 tokens) and mem1 (8 tokens)
        result = self.compiler.compile(query=query, token_budget=18)

        selected_ids = [m.memory_id for m in result.selected_memories]
        selected_contents = [m.content for m in result.selected_memories]

        # Top selected memories must be PostgreSQL related
        self.assertEqual(len(selected_ids), 2)
        self.assertEqual(selected_ids[0], self.mem4.id)  # Constraint PostgreSQL (highest priority)
        self.assertEqual(selected_ids[1], self.mem1.id)  # Database PostgreSQL summary
        self.assertTrue(all("PostgreSQL" in c for c in selected_contents))

        # Unrelated AWS and deadline memories are excluded under budget
        self.assertNotIn(self.mem2.id, selected_ids)
        self.assertNotIn(self.mem3.id, selected_ids)

        excluded_ids = [m.memory_id for m in result.excluded_memories]
        self.assertIn(self.mem2.id, excluded_ids)
        self.assertIn(self.mem3.id, excluded_ids)

    def test_deployment_query_prioritizes_aws(self):
        """
        Query: 'What is our deployment target?'
        Expected: AWS must be prioritized above database and deadline memories.
        """
        query = "What is our deployment target?"
        # Strict token budget of 10 tokens allows only the AWS memory (7 tokens)
        result = self.compiler.compile(query=query, token_budget=10)

        selected_ids = [m.memory_id for m in result.selected_memories]
        self.assertEqual(len(selected_ids), 1)
        self.assertEqual(selected_ids[0], self.mem2.id)  # AWS memory is top prioritized!
        self.assertIn("AWS", result.selected_memories[0].content)

        # Non-matching PostgreSQL and deadline memories are excluded under tight budget
        self.assertNotIn(self.mem1.id, selected_ids)
        self.assertNotIn(self.mem3.id, selected_ids)
        self.assertNotIn(self.mem4.id, selected_ids)



if __name__ == "__main__":
    unittest.main()
