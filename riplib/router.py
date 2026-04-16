from __future__ import annotations

import random
import select
import socket
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from .config import OutputSpec, RouterConfig
from .packet import INFINITY, PacketError, RipEntry, decode_response, encode_response


@dataclass
class Route:
    destination: int
    metric: int
    next_hop: Optional[int]
    timeout_deadline: Optional[float]
    garbage_deadline: Optional[float]
    is_static: bool = False


class RipRouter:
    def __init__(self, config: RouterConfig) -> None:
        self.cfg = config
        self.router_id = config.router_id
        self.neighbors: Dict[int, OutputSpec] = {out.neighbor_id: out for out in config.outputs}
        self.table: Dict[int, Route] = {
            self.router_id: Route(
                destination=self.router_id,
                metric=0,
                next_hop=None,
                timeout_deadline=None,
                garbage_deadline=None,
                is_static=True,
            )
        }

        self.input_sockets: List[socket.socket] = []
        self.send_socket: Optional[socket.socket] = None

        self.triggered_update_pending = False
        self._table_dirty = True
        self._next_periodic_update = self._next_periodic_time(time.monotonic())

    def _next_periodic_time(self, now: float) -> float:
        period = self.cfg.periodic_timer
        if self.cfg.jitter:
            period = random.uniform(0.8 * period, 1.2 * period)
        return now + period

    def _open_sockets(self) -> None:
        for port in self.cfg.input_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("127.0.0.1", port))
            self.input_sockets.append(sock)

        if not self.input_sockets:
            raise RuntimeError("no input sockets created")
        self.send_socket = self.input_sockets[0]

    def _close_sockets(self) -> None:
        for sock in self.input_sockets:
            try:
                sock.close()
            except OSError:
                pass
        self.input_sockets.clear()
        self.send_socket = None

    def run(self) -> None:
        self._open_sockets()
        self._print_table()
        try:
            while True:
                now = time.monotonic()
                timeout = self._compute_select_timeout(now)
                ready, _, _ = select.select(self.input_sockets, [], [], timeout)

                if ready:
                    self._handle_socket_event(ready[0])
                else:
                    self._handle_time_event()
        finally:
            self._close_sockets()

    def _compute_select_timeout(self, now: float) -> float:
        candidates = [max(self._next_periodic_update - now, 0.0)]
        for route in self.table.values():
            if route.destination == self.router_id:
                continue
            if route.metric < INFINITY and route.timeout_deadline is not None:
                candidates.append(max(route.timeout_deadline - now, 0.0))
            if route.metric >= INFINITY and route.garbage_deadline is not None:
                candidates.append(max(route.garbage_deadline - now, 0.0))

        if self.triggered_update_pending:
            candidates.append(0.0)
        return min(candidates) if candidates else 1.0

    def _handle_socket_event(self, sock: socket.socket) -> None:
        try:
            data, _addr = sock.recvfrom(65535)
        except OSError:
            return

        now = time.monotonic()

        try:
            sender_id, entries = decode_response(data)
        except PacketError:
            return

        if sender_id not in self.neighbors:
            return

        neighbor = self.neighbors[sender_id]

        self._learn_or_refresh_direct_neighbor(sender_id, now)

        for entry in entries:
            if entry.destination == self.router_id:
                continue

            incoming_metric = min(INFINITY, neighbor.metric + entry.metric)
            self._update_dynamic_route(entry.destination, sender_id, incoming_metric, now)

        self._expire_timers(now)
        if self._table_dirty:
            self._print_table()
            self._table_dirty = False

    def _handle_time_event(self) -> None:
        now = time.monotonic()
        self._expire_timers(now)

        if now >= self._next_periodic_update:
            self._send_full_update()
            self._next_periodic_update = self._next_periodic_time(now)
            self._table_dirty = True

        if self.triggered_update_pending:
            self._send_full_update()
            self.triggered_update_pending = False

        if self._table_dirty:
            self._print_table()
            self._table_dirty = False

    def _learn_or_refresh_direct_neighbor(self, sender_id: int, now: float) -> None:
        neighbor = self.neighbors[sender_id]
        metric = min(INFINITY, neighbor.metric)

        route = self.table.get(sender_id)
        if route is None:
            self.table[sender_id] = Route(
                destination=sender_id,
                metric=metric,
                next_hop=sender_id,
                timeout_deadline=now + self.cfg.timeout_timer,
                garbage_deadline=None,
            )
            self._table_dirty = True
            return

        changed = route.metric != metric or route.next_hop != sender_id or route.metric >= INFINITY
        route.metric = metric
        route.next_hop = sender_id
        route.timeout_deadline = now + self.cfg.timeout_timer
        route.garbage_deadline = None
        if changed:
            self._table_dirty = True

    def _update_dynamic_route(self, destination: int, next_hop: int, metric: int, now: float) -> None:
        metric = min(metric, INFINITY)
        current = self.table.get(destination)

        if current is None:
            if metric >= INFINITY:
                return
            self.table[destination] = Route(
                destination=destination,
                metric=metric,
                next_hop=next_hop,
                timeout_deadline=now + self.cfg.timeout_timer,
                garbage_deadline=None,
            )
            self._table_dirty = True
            return

        if current.destination == self.router_id:
            return

        if current.next_hop == next_hop:
            if metric >= INFINITY:
                self._invalidate_route(current, now)
                return

            changed = current.metric != metric
            current.metric = metric
            current.timeout_deadline = now + self.cfg.timeout_timer
            current.garbage_deadline = None
            if changed:
                self._table_dirty = True
            return

        if metric < current.metric:
            current.metric = metric
            current.next_hop = next_hop
            current.timeout_deadline = now + self.cfg.timeout_timer
            current.garbage_deadline = None
            self._table_dirty = True

    def _invalidate_route(self, route: Route, now: float) -> None:
        if route.destination == self.router_id:
            return
        if route.metric >= INFINITY and route.garbage_deadline is not None:
            return

        route.metric = INFINITY
        route.timeout_deadline = now + self.cfg.timeout_timer
        route.garbage_deadline = now + self.cfg.garbage_timer
        self.triggered_update_pending = True
        self._table_dirty = True

    def _expire_timers(self, now: float) -> None:
        delete_destinations: List[int] = []

        for destination, route in self.table.items():
            if destination == self.router_id:
                continue

            if route.metric < INFINITY and route.timeout_deadline is not None and now >= route.timeout_deadline:
                self._invalidate_route(route, now)

            if route.metric >= INFINITY and route.garbage_deadline is not None and now >= route.garbage_deadline:
                delete_destinations.append(destination)

        if delete_destinations:
            for destination in delete_destinations:
                self.table.pop(destination, None)
            self._table_dirty = True

    def _send_full_update(self) -> None:
        if self.send_socket is None:
            return

        for neighbor_id, out in self.neighbors.items():
            entries: List[RipEntry] = []
            for destination in sorted(self.table):
                if destination == self.router_id:
                    continue

                route = self.table[destination]
                metric_to_send = route.metric

                if route.next_hop == neighbor_id and route.metric < INFINITY:
                    metric_to_send = INFINITY

                metric_to_send = min(max(1, metric_to_send), INFINITY)
                entries.append(RipEntry(destination=destination, metric=metric_to_send))

            packet = encode_response(self.router_id, entries)
            self.send_socket.sendto(packet, ("127.0.0.1", out.port))

    def _print_table(self) -> None:
        now = time.monotonic()
        print(f"Router {self.router_id} routing table")
        print("destination  metric  next_hop  timeout_left  garbage_left")

        for destination in sorted(self.table):
            route = self.table[destination]
            if destination == self.router_id:
                print(f"{destination:<11} {route.metric:<7} {'-':<8} {'-':<12} {'-':<12}")
                continue

            timeout_left = "-"
            if route.timeout_deadline is not None:
                timeout_left = f"{max(0.0, route.timeout_deadline - now):.1f}s"

            garbage_left = "-"
            if route.garbage_deadline is not None:
                garbage_left = f"{max(0.0, route.garbage_deadline - now):.1f}s"

            next_hop = str(route.next_hop) if route.next_hop is not None else "-"
            print(
                f"{destination:<11} {route.metric:<7} {next_hop:<8} {timeout_left:<12} {garbage_left:<12}"
            )

        print("")
