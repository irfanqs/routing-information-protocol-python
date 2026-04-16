from __future__ import annotations

import unittest

from riplib.config import OutputSpec, RouterConfig
from riplib.packet import INFINITY, decode_response
from riplib.router import RipRouter, Route


class _FakeSocket:
    def __init__(self) -> None:
        self.sent = []

    def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
        self.sent.append((data, addr))


class RouterLogicTests(unittest.TestCase):
    def test_split_horizon_poisoned_reverse(self) -> None:
        cfg = RouterConfig(
            router_id=1,
            input_ports=[6101],
            outputs=[OutputSpec(port=6201, metric=1, neighbor_id=2), OutputSpec(port=6301, metric=1, neighbor_id=3)],
            periodic_timer=5,
            timeout_timer=30,
            garbage_timer=20,
            jitter=False,
        )

        router = RipRouter(cfg)
        router.send_socket = _FakeSocket()
        router.table[2] = Route(2, 1, 2, None, None)
        router.table[4] = Route(4, 2, 2, None, None)
        router.table[5] = Route(5, 3, 3, None, None)

        router._send_full_update()

        sends = router.send_socket.sent
        self.assertEqual(len(sends), 2)

        packet_to_2 = next(data for data, addr in sends if addr[1] == 6201)
        _, entries_to_2 = decode_response(packet_to_2)
        metrics_to_2 = {entry.destination: entry.metric for entry in entries_to_2}
        self.assertEqual(metrics_to_2[4], INFINITY)
        self.assertEqual(metrics_to_2[5], 3)

        packet_to_3 = next(data for data, addr in sends if addr[1] == 6301)
        _, entries_to_3 = decode_response(packet_to_3)
        metrics_to_3 = {entry.destination: entry.metric for entry in entries_to_3}
        self.assertEqual(metrics_to_3[5], INFINITY)
        self.assertEqual(metrics_to_3[4], 2)


if __name__ == "__main__":
    unittest.main()
