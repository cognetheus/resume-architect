import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "resume-architect" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from skill_lint import lint


class SkillLintTests(unittest.TestCase):
    def test_skill_structure(self):
        errors = lint(SCRIPTS.parent)
        self.assertFalse(errors, errors)


if __name__ == "__main__":
    unittest.main()
