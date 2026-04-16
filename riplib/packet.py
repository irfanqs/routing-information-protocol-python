from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterable, List, Tuple

CMD_RESPONSE = 2
VERSION = 2
AFI = 2
INFINITY = 16
MIN_METRIC = 1
MAX_METRIC = 16

_HEADER = struct.Struct("!BBH")
_ENTRY = struct.Struct("!HHIIII")


class PacketError(ValueError):
    """Raised when an incoming RIP packet is malformed."""


@dataclass(frozen=True)
class RipEntry:
    destination: int
    metric: int


def encode_response(sender_router_id: int, entries: Iterable[RipEntry]) -> bytes:
    data = bytearray()
    data.extend(_HEADER.pack(CMD_RESPONSE, VERSION, sender_router_id))

    for entry in entries:
        if not (1 <= entry.destination <= 64000):
            raise PacketError(f"destination out of range: {entry.destination}")
        if not (MIN_METRIC <= entry.metric <= MAX_METRIC):
            raise PacketError(f"metric out of range: {entry.metric}")
        data.extend(_ENTRY.pack(AFI, 0, entry.destination, 0, 0, entry.metric))

    return bytes(data)


def decode_response(data: bytes) -> Tuple[int, List[RipEntry]]:
    if len(data) < _HEADER.size:
        raise PacketError("packet too short for RIP header")
    if (len(data) - _HEADER.size) % _ENTRY.size != 0:
        raise PacketError("packet has incomplete RIP entry")

    command, version, sender_id = _HEADER.unpack_from(data, 0)
    if command != CMD_RESPONSE:
        raise PacketError(f"unsupported command: {command}")
    if version != VERSION:
        raise PacketError(f"unsupported version: {version}")
    if not (1 <= sender_id <= 64000):
        raise PacketError(f"sender router-id out of range: {sender_id}")

    entries: List[RipEntry] = []
    offset = _HEADER.size
    while offset < len(data):
        afi, route_tag, dest, subnet_mask, next_hop, metric = _ENTRY.unpack_from(data, offset)
        offset += _ENTRY.size

        if afi != AFI:
            raise PacketError(f"invalid address family: {afi}")
        if route_tag != 0:
            raise PacketError("route tag must be 0")
        if subnet_mask != 0:
            raise PacketError("subnet mask field must be 0 for this assignment")
        if next_hop != 0:
            raise PacketError("next-hop field must be 0 for this assignment")
        if not (1 <= dest <= 64000):
            raise PacketError(f"destination router-id out of range: {dest}")
        if not (MIN_METRIC <= metric <= MAX_METRIC):
            raise PacketError(f"metric out of range: {metric}")

        entries.append(RipEntry(destination=dest, metric=metric))

    return sender_id, entries
