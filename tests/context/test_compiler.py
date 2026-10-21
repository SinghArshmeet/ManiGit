"""
Unit and integration tests for ContextCompiler.
"""

import os
import tempfile
import unittest

from manigit.context.compiler import ContextCompiler
from manigit.core.models import MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestContextCompiler(unittest.TestCase):
    """Test suite for ContextCompiler execution, historical compilation, and immutability."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "compiler_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.root_branch = self.repo.initialize_repository()

        # Seed messages and memories
        self.m1 = self.repo.append_message("s1", MessageRole.USER, "Constraint: Database must use SQLite.")
        self.m2 = self.repo.append_message("s1", MessageRole.USER, "Constraint: Max token limit is 4096.")
        self.m3 = self.repo.append_message("s1", MessageRole.USER, "Feature: UI has dark mode.")

        self.mem1 = self.repo.create_memory("Database = SQLite", MemoryTier.VERBATIM, [self.m1.id])
        self.mem2 = self.repo.create_memory("Token Limit = 4096", MemoryTier.VERBATIM, [self.m2.id])
        self.mem3 = self.repo.create_memory("Theme = Dark Mode", MemoryTier.VERBATIM, [self.m3.id])

        # Commit 1 on main: mem1
        self.c1 = self.repo.create_commit("Add DB constraint", "Step 1", [self.mem1.id])
        # Commit 2 on main: mem1 + mem2
        self.c2 = self.repo.create_commit("Add token limit", "Step 2", [self.mem1.id, self.mem2.id])

        self.compiler = ContextCompiler(self.repo)

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_historical_commit_context_without_head_leakage(self):
        """
        Verify that compiling with commit_id=c1 reconstructs ONLY memories present at c1,
        and does NOT leak c2 memories into context.
        """
        # Query at historical commit c1
        result_c1 = self.compiler.compile(
            query="token limit settings",
            token_budget=1000,
            commit_id=self.c1.id,
        )

        selected_ids_c1 = [m.memory_id for m in result_c1.selected_memories]
        # At c1, mem2 was not yet created/committed
        self.assertNotIn(self.mem2.id, selected_ids_c1)
        self.assertIn(self.mem1.id, selected_ids_c1)
        self.assertEqual(result_c1.commit_id, self.c1.id)

        # Query at c2 (current HEAD)
        result_c2 = self.compiler.compile(
            query="token limit settings",
            token_budget=1000,
            commit_id=self.c2.id,
        )
        selected_ids_c2 = [m.memory_id for m in result_c2.selected_memories]
        self.assertIn(self.mem2.id, selected_ids_c2)

    def test_branch_aware_compilation(self):
        """
        Verify that different branches maintain isolated context compilation.
        main: has mem1 + mem2
        exp-ui: has mem1 + mem3
        """
        self.repo.create_branch("exp-ui", source_commit_id=self.c1.id)
        self.repo.switch_branch("exp-ui")
        c_exp = self.repo.create_commit("Add dark mode UI", "Exp step", [self.mem1.id, self.mem3.id])

        # Compile for main
        res_main = self.compiler.compile(query="dark mode", token_budget=1000, branch="main")
        main_ids = [m.memory_id for m in res_main.selected_memories]
        self.assertNotIn(self.mem3.id, main_ids)

        # Compile for exp-ui
        res_exp = self.compiler.compile(query="dark mode", token_budget=1000, branch="exp-ui")
        exp_ids = [m.memory_id for m in res_exp.selected_memories]
        self.assertIn(self.mem3.id, exp_ids)

    def test_context_compiler_is_read_only(self):
        """
        Verify compiler execution produces zero mutations in database tables:
        messages, memories, memory_sources, commits, commit_memories, branches.
        Also verify that active branch remains completely unchanged.
        """
        active_branch_before = self.repo.active_branch
        commits_before = len(self.repo.get_commit_history("main"))
        branches_before = len(self.repo.list_branches())

        conn = self.repo.db.connect()
        counts_before = {
            "messages": conn.execute("SELECT count(*) as c FROM messages").fetchone()["c"],
            "memories": conn.execute("SELECT count(*) as c FROM memories").fetchone()["c"],
            "memory_sources": conn.execute("SELECT count(*) as c FROM memory_sources").fetchone()["c"],
            "commits": conn.execute("SELECT count(*) as c FROM commits").fetchone()["c"],
            "commit_memories": conn.execute("SELECT count(*) as c FROM commit_memories").fetchone()["c"],
            "branches": conn.execute("SELECT count(*) as c FROM branches").fetchone()["c"],
        }

        # Run several compilations across queries, branches, and historical commits
        self.compiler.compile("database", 500)
        self.compiler.compile("dark mode", 500, branch="main")
        self.compiler.compile("token limit", 500, commit_id=self.c1.id)
        self.compiler.compile("nonexistent topic", 50)

        counts_after = {
            "messages": conn.execute("SELECT count(*) as c FROM messages").fetchone()["c"],
            "memories": conn.execute("SELECT count(*) as c FROM memories").fetchone()["c"],
            "memory_sources": conn.execute("SELECT count(*) as c FROM memory_sources").fetchone()["c"],
            "commits": conn.execute("SELECT count(*) as c FROM commits").fetchone()["c"],
            "commit_memories": conn.execute("SELECT count(*) as c FROM commit_memories").fetchone()["c"],
            "branches": conn.execute("SELECT count(*) as c FROM branches").fetchone()["c"],
        }

        commits_after = len(self.repo.get_commit_history("main"))
        branches_after = len(self.repo.list_branches())

        self.assertEqual(self.repo.active_branch, active_branch_before)
        self.assertEqual(commits_before, commits_after)
        self.assertEqual(branches_before, branches_after)
        self.assertEqual(counts_before, counts_after)

    def test_deterministic_compilation(self):
        """
        Verify identical inputs produce identical ContextResults down to token counts and order.
        """
        res1 = self.compiler.compile(query="database sqlite", token_budget=500)
        res2 = self.compiler.compile(query="database sqlite", token_budget=500)

        self.assertEqual(res1.to_dict(), res2.to_dict())
        self.assertEqual(res1.to_prompt_context(), res2.to_prompt_context())

    def test_prompt_formatting(self):
        """Verify to_prompt_context() generates structured block."""
        res = self.compiler.compile(query="database sqlite", token_budget=500)
        formatted = res.to_prompt_context()
        self.assertIn("[Active Memory Context]", formatted)
        self.assertIn("[VERBATIM] Database = SQLite", formatted)

    def test_provenance_traceability_in_context_result(self):
        """
        Verify end-to-end provenance traceability:
        memory_id -> source_message_ids -> tier -> confidence -> commit/state.
        Also verify that later commits and branch modifications do not alter
        the provenance or content of historical commit compilation.
        """
        # Historical compilation at c1
        res_c1 = self.compiler.compile(query="database", token_budget=500, commit_id=self.c1.id)
        self.assertEqual(res_c1.commit_id, self.c1.id)
        self.assertEqual(len(res_c1.selected_memories), 1)

        selected = res_c1.selected_memories[0]
        self.assertEqual(selected.memory_id, self.mem1.id)
        self.assertEqual(selected.source_message_ids, [self.m1.id])
        self.assertEqual(selected.tier, MemoryTier.VERBATIM.value)
        self.assertIsInstance(selected.confidence, float)

        # Append new messages and create a newer commit on main
        m_late = self.repo.append_message("s1", MessageRole.USER, "New late message after c2.")
        mem_late = self.repo.create_memory("Late Memory", MemoryTier.VERBATIM, [m_late.id])
        c3 = self.repo.create_commit("Commit 3", "Late commit", [self.mem1.id, self.mem2.id, mem_late.id])

        # Re-compile at c1: must be 100% identical, no leakage of c2 or c3, provenance untouched
        res_c1_repeat = self.compiler.compile(query="database", token_budget=500, commit_id=self.c1.id)
        self.assertEqual(res_c1_repeat.to_dict(), res_c1.to_dict())
        self.assertNotIn(mem_late.id, [m.memory_id for m in res_c1_repeat.selected_memories])
        self.assertNotIn(self.mem2.id, [m.memory_id for m in res_c1_repeat.selected_memories])


if __name__ == "__main__":
    unittest.main()

