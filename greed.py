"""
Greed – closed-loop orchestration entry point.

Runs the three-stage pipeline:
  1. Signal  – detect the most profitable trending price
  2. Logic   – map the price event to an operational action
  3. Execute – deploy the action via the Jamf Now fleet layer
"""

import argparse
import sys

from deployment import JamfNowDeployer
from mapping import build_default_mapper
from price_signal import PriceFeed, detect_trending_peak


def run(
    asset: str = "GREED",
    base_price: float = 100.0,
    profit_threshold: float = 110.0,
    volatility: float = 6.0,
    fleet_size: int = 10,
    ticks: int = 50,
    tick_interval: float = 0.1,
) -> None:
    print("=== Greed: closed-loop orchestration started ===")
    print(
        f"Asset={asset}  base={base_price}  threshold={profit_threshold}  "
        f"fleet={fleet_size}  ticks={ticks}\n"
    )

    feed = PriceFeed(
        asset=asset,
        base_price=base_price,
        volatility=volatility,
        profit_threshold=profit_threshold,
        tick_interval=tick_interval,
    )
    mapper = build_default_mapper(profit_threshold=profit_threshold)
    deployer = JamfNowDeployer(fleet_size=fleet_size)

    deployments = 0
    for event in detect_trending_peak(feed, window=5):
        print(f"[signal] Profitable peak detected: {event.asset}@{event.price:.2f}")

        action = mapper.resolve(event)
        if action is None:
            print("  [mapping] No matching action for this event – skipping.")
            continue

        deployer.deploy(action, event)
        deployments += 1

        # Stop after the configured number of ticks have been consumed.
        # detect_trending_peak itself drives the feed; we count deployments here.
        if deployments >= max(1, ticks // 10):
            break

    deployer.summary()
    print("\n=== Greed: session complete ===")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Greed – signal-to-fleet orchestration loop"
    )
    parser.add_argument("--asset", default="GREED")
    parser.add_argument("--base-price", type=float, default=100.0)
    parser.add_argument("--threshold", type=float, default=110.0)
    parser.add_argument("--volatility", type=float, default=6.0)
    parser.add_argument("--fleet-size", type=int, default=10)
    parser.add_argument("--ticks", type=int, default=50,
                        help="Number of price ticks to simulate before stopping")
    parser.add_argument("--tick-interval", type=float, default=0.1,
                        help="Seconds between simulated ticks")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    run(
        asset=args.asset,
        base_price=args.base_price,
        profit_threshold=args.threshold,
        volatility=args.volatility,
        fleet_size=args.fleet_size,
        ticks=args.ticks,
        tick_interval=args.tick_interval,
    )
"""
Signal layer: monitors a live price feed and detects profitable trending conditions.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class PriceEvent:
    asset: str
    price: float
    threshold: float = 0.0
    timestamp: float = field(default_factory=lambda: time.time())

    @property
    def is_profitable(self) -> bool:
        return self.price >= self.threshold


class PriceFeed:
    """Simulates a live market or pricing feed."""

    def __init__(
        self,
        asset: str = "GREED",
        base_price: float = 100.0,
        volatility: float = 5.0,
        profit_threshold: float = 110.0,
        tick_interval: float = 0.5,
    ) -> None:
        self.asset = asset
        self.base_price = base_price
        self.volatility = volatility
        self.profit_threshold = profit_threshold
        self.tick_interval = tick_interval
        self._current_price = base_price

    def _next_price(self) -> float:
        delta = random.gauss(0, self.volatility)
        # Mean-revert slightly toward base to avoid drift.
        reversion = (self.base_price - self._current_price) * 0.05
        self._current_price = max(0.01, self._current_price + delta + reversion)
        return round(self._current_price, 2)

    def stream(self, ticks: int = 0) -> Iterator[PriceEvent]:
        """Yield PriceEvent objects. If *ticks* is 0 the stream is infinite."""
        count = 0
        while ticks == 0 or count < ticks:
            price = self._next_price()
            event = PriceEvent(
                asset=self.asset,
                price=price,
                threshold=self.profit_threshold,
            )
            yield event
            count += 1
            time.sleep(self.tick_interval)


def detect_trending_peak(feed: PriceFeed, window: int = 5) -> Iterator[PriceEvent]:
    """Yield only the events that represent a trending peak above the threshold.

    A peak is defined as a price that is both above the profit threshold and
    higher than all prices in the preceding *window* ticks.
    """
    history: list[float] = []
    for event in feed.stream():
        history.append(event.price)
        if len(history) > window:
            history.pop(0)
        if event.is_profitable and event.price == max(history):
            yield event
"""
Mapping layer: translates a profitable price event into a predefined operational action.
"""

from dataclasses import dataclass
from typing import Callable

from price_signal import PriceEvent


@dataclass
class Action:
    name: str
    package: str
    description: str
    handler: Callable[["Action", PriceEvent], None]

    def execute(self, event: PriceEvent) -> None:
        self.handler(self, event)


class ActionMapper:
    """Maps price conditions to registered operational actions."""

    def __init__(self) -> None:
        self._rules: list[tuple[Callable[[PriceEvent], bool], Action]] = []

    def register(
        self, condition: Callable[[PriceEvent], bool], action: Action
    ) -> None:
        """Register an *action* to fire when *condition* returns True."""
        self._rules.append((condition, action))

    def resolve(self, event: PriceEvent) -> Action | None:
        """Return the first action whose condition matches *event*, or None."""
        for condition, action in self._rules:
            if condition(event):
                return action
        return None


# ---------------------------------------------------------------------------
# Default rule set
# ---------------------------------------------------------------------------

def _log_action(action: Action, event: PriceEvent) -> None:
    print(
        f"  [action] '{action.name}' triggered by {event.asset}@{event.price:.2f} "
        f"(package: {action.package})"
    )


def build_default_mapper(profit_threshold: float = 110.0) -> ActionMapper:
    """Return an ActionMapper pre-loaded with the default rule set."""
    mapper = ActionMapper()

    mapper.register(
        condition=lambda e: e.price >= profit_threshold * 1.2,
        action=Action(
            name="high-profit-deploy",
            package="greed-premium-toolkit-1.0.pkg",
            description="Deploy premium toolkit to entire fleet on peak profit signal.",
            handler=_log_action,
        ),
    )

    mapper.register(
        condition=lambda e: e.price >= profit_threshold,
        action=Action(
            name="standard-profit-deploy",
            package="greed-standard-toolkit-1.0.pkg",
            description="Deploy standard toolkit when profit threshold is crossed.",
            handler=_log_action,
        ),
    )

    return mapper
"""
Deployment layer: simulates Jamf Now fleet deployment of a selected package.
"""

import random
import time
from dataclasses import dataclass, field

from mapping import Action
from price_signal import PriceEvent


@dataclass
class DeploymentRecord:
    action: Action
    event: PriceEvent
    device_count: int
    success: bool
    timestamp: float = field(default_factory=lambda: time.time())

    def __str__(self) -> str:
        status = "OK" if self.success else "FAILED"
        return (
            f"[{status}] {self.action.package} → {self.device_count} device(s) "
            f"@ {self.event.asset}={self.event.price:.2f}"
        )


class JamfNowDeployer:
    """Simulates the Jamf Now Blueprint deployment pipeline.

    In a real implementation this class would call the Jamf Now REST API to:
      1. Upload the .pkg file to the distribution point.
      2. Attach it to a Blueprint.
      3. Push the Blueprint to all managed devices.
    """

    def __init__(
        self,
        fleet_size: int = 10,
        simulate_failure_rate: float = 0.05,
    ) -> None:
        self.fleet_size = fleet_size
        self.simulate_failure_rate = simulate_failure_rate
        self.history: list[DeploymentRecord] = []

    def deploy(self, action: Action, event: PriceEvent) -> DeploymentRecord:
        """Push *action.package* to the entire managed fleet.

        Returns a DeploymentRecord describing the outcome.
        """
        print(f"  [deploy] Pushing '{action.package}' to {self.fleet_size} device(s) …")

        # Simulate network/API latency.
        time.sleep(0.1)

        success = random.random() > self.simulate_failure_rate
        record = DeploymentRecord(
            action=action,
            event=event,
            device_count=self.fleet_size,
            success=success,
        )
        self.history.append(record)
        print(f"  [deploy] {record}")
        return record

    def summary(self) -> None:
        """Print a summary of all deployments made in this session."""
        total = len(self.history)
        succeeded = sum(1 for r in self.history if r.success)
        print(f"\n=== Deployment summary: {succeeded}/{total} succeeded ===")
        for record in self.history:
            print(f"  {record}")
