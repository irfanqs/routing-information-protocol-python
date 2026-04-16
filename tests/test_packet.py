from __future__ import annotations

import unittest

from riplib.packet import PacketError, RipEntry, decode_response, encode_response


class PacketTests(unittest.TestCase):
    def test_encode_decode_roundtrip(self) -> None:
        packet = encode_response(
            sender_router_id=7,
            entries=[RipEntry(destination=10, metric=1), RipEntry(destination=11, metric=16)],
        )

        sender, entries = decode_response(packet)
        self.assertEqual(sender, 7)
        self.assertEqual(entries[0].destination, 10)
        self.assertEqual(entries[0].metric, 1)
        self.assertEqual(entries[1].metric, 16)

    def test_reject_invalid_metric_on_decode(self) -> None:
        packet = bytearray(encode_response(sender_router_id=7, entries=[RipEntry(destination=10, metric=1)]))
        packet[-1] = 17

        with self.assertRaises(PacketError):
            decode_response(bytes(packet))


if __name__ == "__main__":
    unittest.main()
