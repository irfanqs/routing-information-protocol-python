from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riplib.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def _write_temp(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return Path(tmp.name)

    def test_valid_config(self) -> None:
        cfg_path = self._write_temp(
            "\n".join(
                [
                    "router-id 10",
                    "input-ports 6110, 6201",
                    "outputs 7001-1-20, 7002-5-30",
                    "periodic-timer 2",
                    "timeout-timer 12",
                    "garbage-timer 8",
                    "jitter false",
                ]
            )
        )

        cfg = load_config(cfg_path)
        self.assertEqual(cfg.router_id, 10)
        self.assertEqual(cfg.input_ports, [6110, 6201])
        self.assertEqual(len(cfg.outputs), 2)
        self.assertFalse(cfg.jitter)

    def test_reject_overlapping_input_and_output_ports(self) -> None:
        cfg_path = self._write_temp(
            "\n".join(
                [
                    "router-id 10",
                    "input-ports 6110, 6201",
                    "outputs 6110-1-20",
                ]
            )
        )

        with self.assertRaises(ConfigError):
            load_config(cfg_path)


if __name__ == "__main__":
    unittest.main()
