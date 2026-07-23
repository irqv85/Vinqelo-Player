from __future__ import annotations

import unittest

from ui.system_tray import progress_percent


class ExportProgressTests(unittest.TestCase):
    def test_progress_percent_is_bounded(self) -> None:
        self.assertEqual(progress_percent(0, 0), 0)
        self.assertEqual(progress_percent(1, 4), 25)
        self.assertEqual(progress_percent(3, 4), 75)
        self.assertEqual(progress_percent(10, 4), 100)
        self.assertEqual(progress_percent(-1, 4), 0)


if __name__ == "__main__":
    unittest.main()
