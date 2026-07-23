from __future__ import annotations

import os
import subprocess
import unittest

from library.process_utils import hidden_low_priority_process_options


class ProcessOptionsTests(unittest.TestCase):
    def test_conversion_process_is_hidden_and_low_priority_on_windows(self) -> None:
        options = hidden_low_priority_process_options()
        if os.name != "nt":
            self.assertEqual(options, {})
            return

        flags = int(options["creationflags"])
        self.assertTrue(flags & subprocess.CREATE_NO_WINDOW)
        self.assertTrue(flags & subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        startupinfo = options["startupinfo"]
        self.assertTrue(startupinfo.dwFlags & subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(startupinfo.wShowWindow, subprocess.SW_HIDE)


if __name__ == "__main__":
    unittest.main()
