from __future__ import annotations

"""
symbol_lab.py

A small experimental lab for Darrell's symbols project.

What this file does:
1. Models exact equality vs approximate equality.
2. Tracks Xerox-style drift across a chain of transformations.
3. Forces a Na/HOLD state when drift exceeds a threshold.
4. Lets us test ideas at the edges instead of only in the middle.
5. Includes a simple "top stability" model:
   balanced support around center = stable
   imbalance = wobble

This is intentionally written to be easy to read, edit, and extend.
"""

# ============================================================
# README-STYLE HEADER
# ============================================================
# PURPOSE
# - symbol_lab.py is a small experimental symbolic reasoning lab.
# - It demonstrates equality, approximation, drift, hold-state behavior,
#   path-vs-outcome evaluation, and case ranking/explanation.
#
# CORE OPERATORS
# - "="       exact equality
# - "≈"       approximate equality within tolerance
# - "Δ"       transformation / accumulated drift
# - "τ"       path drift threshold
# - "ε"       outcome/origin threshold
# - "Na"      hold / do not resolve
# - "RESOLVE" maps state into action
#
# CORE STATES
# - READY           path and outcome are both acceptable
# - UNSTABLE_MATCH  outcome is acceptable but path drift is too high
# - NA/HOLD         hold state; drift/outcome checks failed for safe resolve
#
# WHAT THE DEMOS PROVE
# - many equations can resolve to 4
# - same numeric result does not guarantee same trust quality
# - path integrity and outcome accuracy must both be considered
# - the lab can evaluate, classify, resolve, rank, and explain
# ============================================================

from dataclasses import dataclass, field
import re
from typing import Any, Callable, List, Tuple


# =========================
# CORE DATA STRUCTURES
# =========================


@dataclass
class StepResult:
    """Represents one transformation step in a chain."""
    name: str
    value: float
    local_drift: float
    total_drift: float


@dataclass
class DriftChain:
    """
    Holds the results of a chain of transformations.

    start_value:
        The original value we began with.

    tau:
        The maximum allowed total drift before we force HOLD/Na.

    epsilon:
        The maximum allowed final distance from origin.
        This is the outcome gate (where we ended), while tau is
        the path gate (how much drift accumulated along the way).
    """
    start_value: float
    tau: float
    epsilon: float = 0.1
    steps: List[StepResult] = field(default_factory=list)
    _override_current_value: float | None = field(default=None, init=False, repr=False)
    _override_total_drift: float | None = field(default=None, init=False, repr=False)
    _override_copy_depth: int | None = field(default=None, init=False, repr=False)

    @property
    def current_value(self) -> float:
        """Return the latest value in the chain."""
        if self._override_current_value is not None:
            return self._override_current_value
        if not self.steps:
            return self.start_value
        return self.steps[-1].value

    @property
    def total_drift(self) -> float:
        """Return the total accumulated drift so far."""
        if self._override_total_drift is not None:
            return self._override_total_drift
        if not self.steps:
            return 0.0
        return self.steps[-1].total_drift

    @property
    def copy_depth(self) -> int:
        """
        Return how many copy/transformation steps have been applied.

        This is a direct chain-depth indicator:
        - 0 means still at origin (no copies yet)
        - N means N transformations were performed
        """
        if self._override_copy_depth is not None:
            return self._override_copy_depth
        return len(self.steps)

    @property
    def origin_distance(self) -> float:
        """
        Return absolute distance from the original start value.

        This complements total_drift:
        - total_drift measures path length traveled
        - origin_distance measures where we ended relative to origin
        """
        return abs(self.current_value - self.start_value)

    @property
    def outcome_ok(self) -> bool:
        """
        Return True if the final outcome is close enough to origin.

        This is the epsilon gate:
        outcome_ok = origin_distance <= epsilon
        """
        return self.origin_distance <= self.epsilon

    @property
    def path_ok(self) -> bool:
        """
        Return True if total path drift stayed within tau.

        This is the path gate:
        path_ok = total_drift <= tau
        """
        return self.total_drift <= self.tau

    @property
    def state(self) -> str:
        """
        Return the dual-gate system state.

        READY:
            path_ok AND outcome_ok

        NA/HOLD:
            NOT path_ok AND NOT outcome_ok

        UNSTABLE_MATCH:
            NOT path_ok AND outcome_ok

        Remaining gate combination (path_ok AND NOT outcome_ok):
            treated as NA/HOLD because outcome target was not met.
            We keep state outputs constrained to the three required values.
        """
        if self.path_ok and self.outcome_ok:
            return "READY"
        if (not self.path_ok) and (not self.outcome_ok):
            return "NA/HOLD"
        if (not self.path_ok) and self.outcome_ok:
            return "UNSTABLE_MATCH"
        return "NA/HOLD"

    def add_step(self, name: str, new_value: float) -> None:
        """
        Add one transformation step.

        local_drift is measured relative to the previous value.
        total_drift accumulates all local drift.
        """
        # If the chain had synthetic overrides from a demo helper,
        # real step insertion clears those overrides and returns to
        # normal step-derived behavior.
        self._clear_overrides()
        previous = self.current_value
        local_drift = abs(new_value - previous)
        running_total = self.total_drift + local_drift
        self.steps.append(
            StepResult(
                name=name,
                value=new_value,
                local_drift=local_drift,
                total_drift=running_total,
            )
        )

    def _clear_overrides(self) -> None:
        """Clear synthetic terminal overrides and use step-derived values only."""
        self._override_current_value = None
        self._override_total_drift = None
        self._override_copy_depth = None

    def set_simulated_terminal_state(
        self,
        copy_depth: int,
        total_drift: float,
        current_value: float,
    ) -> None:
        """
        Set a minimal synthetic terminal state for expression demos.

        This is intentionally tiny and read-friendly:
        - no intermediate steps are fabricated
        - only terminal metrics needed by state logic are set
        """
        if copy_depth < 0:
            raise ValueError("copy_depth must be >= 0")
        if total_drift < 0:
            raise ValueError("total_drift must be >= 0")
        self.steps = []
        self._override_copy_depth = copy_depth
        self._override_total_drift = total_drift
        self._override_current_value = current_value

    def report(self) -> str:
        """Return a readable report of the chain."""
        lines = []
        lines.append("=" * 60)
        lines.append("DRIFT CHAIN REPORT")
        lines.append("=" * 60)
        lines.append(f"Start value: {self.start_value}")
        lines.append(f"Tau (allowed drift threshold): {self.tau}")
        lines.append(f"Epsilon (allowed origin distance): {self.epsilon}")
        lines.append("")

        if not self.steps:
            lines.append("No steps recorded yet.")
        else:
            for i, step in enumerate(self.steps, start=1):
                lines.append(
                    f"Step {i}: {step.name:20s} | "
                    f"value={step.value:8.4f} | "
                    f"local_drift={step.local_drift:8.4f} | "
                    f"total_drift={step.total_drift:8.4f}"
                )

        lines.append("")
        lines.append(f"Copy depth: {self.copy_depth}")
        lines.append(f"Origin distance: {self.origin_distance:.4f}")
        lines.append(f"Path OK: {self.path_ok}")
        lines.append(f"Outcome OK: {self.outcome_ok}")
        lines.append(f"Final state: {self.state}")
        if self.state == "READY":
            lines.append("Meaning: path and outcome are both acceptable.")
        elif self.state == "UNSTABLE_MATCH":
            lines.append("Meaning: final outcome matches origin, but path drift was unstable.")
        else:
            lines.append("Meaning: hold; gates were not jointly satisfied.")
        return "\n".join(lines)


# =========================
# EQUALITY / APPROXIMATION
# =========================


def exact_equal(a: float, b: float) -> bool:
    """True only if values are exactly equal."""
    return a == b


def approx_equal(a: float, b: float, tau: float) -> bool:
    """True if values are within the allowed tolerance tau."""
    return abs(a - b) <= tau


# =========================
# SYMBOL OPERATOR ENGINE
# =========================
#
# This section introduces a tiny symbolic operator layer.
# The goal is NOT to over-engineer; it is just to make the
# project's symbols explicit and reusable while keeping the
# script easy to read.
#
# Philosophy mapping:
# "="  -> exact equivalence
# "≈"  -> approximate equivalence within tolerance
# "Δ"  -> accumulated Xerox-style drift
# "Na" -> hold / do not resolve / require new evidence


@dataclass
class SymbolOperator:
    """
    Base operator metadata container.

    All concrete operators inherit this shape so each symbol has:
    - a human-readable name
    - a glyph
    - a plain-language description
    """
    name: str
    glyph: str
    description: str

    def apply(self, *args, **kwargs):
        """
        Abstract-style operator method.

        Concrete operators must implement this.
        """
        raise NotImplementedError("SymbolOperator.apply() must be implemented by subclasses.")


@dataclass
class EqualsOperator(SymbolOperator):
    """
    "=" operator.

    True only when values are exactly equal.
    """

    def apply(self, a: float, b: float) -> bool:
        return a == b


@dataclass
class ApproxOperator(SymbolOperator):
    """
    "≈" operator.

    True when values are close enough under tolerance tau.
    """

    def apply(self, a: float, b: float, tau: float) -> bool:
        return abs(a - b) <= tau


@dataclass
class DriftOperator(SymbolOperator):
    """
    "Δ" operator.

    Reads a DriftChain and returns a compact drift-state summary.
    """

    def apply(self, chain: DriftChain) -> dict[str, Any]:
        return {
            "start_value": chain.start_value,
            "current_value": chain.current_value,
            "copy_depth": chain.copy_depth,
            "origin_distance": chain.origin_distance,
            "total_drift": chain.total_drift,
            "tau": chain.tau,
            "epsilon": chain.epsilon,
            "path_ok": chain.path_ok,
            "outcome_ok": chain.outcome_ok,
            "state": chain.state,
        }


@dataclass
class NaOperator(SymbolOperator):
    """
    "Na" operator.

    Returns an explicit HOLD payload to indicate do-not-resolve.
    """

    def apply(self, reason: str) -> dict[str, str]:
        return {
            "state": "NA/HOLD",
            "reason": reason,
        }


@dataclass
class ResolveOperator(SymbolOperator):
    """
    Minimal resolution operator.

    It converts drift-state output into an explicit action channel:
    - ACCEPT
    - BLOCK
    - FLAG
    """

    def apply(self, state: str) -> dict[str, str]:
        mapping = {
            "READY": {
                "action": "ACCEPT",
                "reason": "path and outcome verified",
            },
            "NA/HOLD": {
                "action": "BLOCK",
                "reason": "drift or outcome invalid",
            },
            "UNSTABLE_MATCH": {
                "action": "FLAG",
                "reason": "outcome valid but path unstable",
            },
        }
        resolved = mapping.get(
            state,
            {
                "action": "BLOCK",
                "reason": "drift or outcome invalid",
            },
        )
        return {
            "state": state,
            "action": resolved["action"],
            "reason": resolved["reason"],
        }


@dataclass
class ExpressionCase:
    """
    Compact expression-evaluation record for the 'many equations = 4' demo.

    The numeric expression result is captured separately from the simulated
    drift posture so we can inspect both syntax correctness and path quality.
    """
    name: str
    expression: str
    expected_value: float
    computed_value: float
    copy_depth: int
    total_drift: float
    origin_distance: float
    state: str
    action: str
    caution_label: str


def evaluate_expression_case(
    name: str,
    expression: str,
    expected_value: float,
    simulated_copy_depth: int,
    simulated_total_drift: float,
    simulated_origin_distance: float,
    tau: float,
    epsilon: float,
) -> ExpressionCase:
    """
    Evaluate one expression case with a minimal synthetic drift terminal state.

    Security posture for demo eval:
    - no builtins
    - no external symbols
    """
    computed_value = float(eval(expression, {"__builtins__": {}}, {}))

    chain = DriftChain(start_value=expected_value, tau=tau, epsilon=epsilon)
    chain.set_simulated_terminal_state(
        copy_depth=simulated_copy_depth,
        total_drift=simulated_total_drift,
        current_value=expected_value + simulated_origin_distance,
    )

    state = chain.state
    action = RESOLVE.apply(state)["action"]
    caution_label = get_live_caution_label(chain.total_drift, tau)

    return ExpressionCase(
        name=name,
        expression=expression,
        expected_value=expected_value,
        computed_value=computed_value,
        copy_depth=chain.copy_depth,
        total_drift=chain.total_drift,
        origin_distance=chain.origin_distance,
        state=state,
        action=action,
        caution_label=caution_label,
    )


def build_many_equations_equal_four_cases() -> list[ExpressionCase]:
    """
    Build the canonical four expression cases used across demos.

    This keeps case data in one place so reporting, ranking, and
    explanation demos stay behavior-identical while avoiding repetition.
    """
    tau = 1.0
    epsilon = 0.1
    return [
        evaluate_expression_case(
            name="clean_four",
            expression="2 + 2",
            expected_value=4.0,
            simulated_copy_depth=1,
            simulated_total_drift=0.0,
            simulated_origin_distance=0.0,
            tau=tau,
            epsilon=epsilon,
        ),
        evaluate_expression_case(
            name="approx_four",
            expression="3.999 + 0.001",
            expected_value=4.0,
            simulated_copy_depth=2,
            simulated_total_drift=0.02,
            simulated_origin_distance=0.0,
            tau=tau,
            epsilon=epsilon,
        ),
        evaluate_expression_case(
            name="unstable_four",
            expression="(4.6 - 0.6)",
            expected_value=4.0,
            simulated_copy_depth=3,
            simulated_total_drift=1.2,
            simulated_origin_distance=0.0,
            tau=tau,
            epsilon=epsilon,
        ),
        evaluate_expression_case(
            name="bad_four",
            expression="4.2",
            expected_value=4.0,
            simulated_copy_depth=1,
            simulated_total_drift=0.2,
            simulated_origin_distance=0.2,
            tau=tau,
            epsilon=epsilon,
        ),
    ]


def estimate_copy_depth(expression: str) -> int:
    """
    Estimate copy depth from a simple operator count.

    Heuristic only:
    - counts +, -, *, /, %, **
    - returns at least 1
    """
    power_count = expression.count("**")
    # Remove power operators so "*" is not double-counted.
    remainder = expression.replace("**", "")
    operator_count = (
        power_count
        + remainder.count("+")
        + remainder.count("-")
        + remainder.count("*")
        + remainder.count("/")
        + remainder.count("%")
    )
    return max(1, operator_count)


def get_live_caution_label(
    total_drift: float,
    tau: float,
) -> str:
    """
    Return a lightweight caution label for reporting.

    This is an audit/reporting layer only. It does not replace
    or override the core READY / UNSTABLE_MATCH / NA-HOLD state machine.
    """
    if total_drift < 0.25:
        return "CLEAN"
    if total_drift < tau:
        return "CAUTION"
    return "UNSTABLE"


def estimate_structural_drift(
    expression: str,
    expected_value: float,
) -> float:
    """
    Estimate structural drift from numeric literal layout.

    This uses a lightweight regex extraction of numeric literals and
    adds a small extra penalty for subtraction-style cancellation paths
    around the expected value.
    """
    numeric_tokens = re.findall(r"\d*\.?\d+(?:[eE][-+]?\d+)?", expression)
    if not numeric_tokens:
        return 0.0

    literals = [float(token) for token in numeric_tokens]
    distances = [abs(value - expected_value) for value in literals]

    # Baseline structure cost from how far literals sit from expected.
    average_distance = sum(distances) / len(distances)
    baseline_penalty = average_distance * 0.04

    # Extra cancellation-path penalty:
    # subtraction with literals on both sides of expected can "cancel"
    # to target while still reflecting unstable structure.
    cancellation_penalty = 0.0
    if "-" in expression and any(value > expected_value for value in literals) and any(
        value < expected_value for value in literals
    ):
        cancellation_penalty = 0.35

    return baseline_penalty + cancellation_penalty


def estimate_total_drift(
    computed_value: float,
    expected_value: float,
    copy_depth: int,
    expression: str,
) -> float:
    """
    First-pass drift heuristic for live expression batches.

    total_drift =
        origin_distance + structural depth penalty + structural expression penalty
    where:
        origin_distance = abs(computed - expected)
        structural depth penalty = max(0, depth - 1) * 0.05
        structural expression penalty = estimate_structural_drift(expression, expected)
    """
    origin_distance = abs(computed_value - expected_value)
    depth_penalty = max(0, copy_depth - 1) * 0.05
    structural_penalty = estimate_structural_drift(expression, expected_value)

    # Still heuristic: this tries to separate clean convergence from
    # suspicious cancellation paths without pretending full symbolic parsing.
    return origin_distance + depth_penalty + structural_penalty


def run_expression_batch(
    expressions: list[str],
    expected_value: float = 4.0,
    tau: float = 1.0,
    epsilon: float = 0.1,
) -> list[ExpressionCase]:
    """
    Evaluate a live batch of expressions into ExpressionCase records.

    This reuses the existing expression-case path and only adds
    lightweight copy-depth and drift heuristics.
    """
    cases: list[ExpressionCase] = []
    for index, expression in enumerate(expressions, start=1):
        computed_value = float(eval(expression, {"__builtins__": {}}, {}))
        copy_depth = estimate_copy_depth(expression)
        origin_distance = abs(computed_value - expected_value)
        total_drift = estimate_total_drift(
            computed_value,
            expected_value,
            copy_depth,
            expression,
        )

        # Reuse the existing case-construction logic so state/action
        # behavior remains centralized.
        case = evaluate_expression_case(
            name=f"batch_case_{index}",
            expression=expression,
            expected_value=expected_value,
            simulated_copy_depth=copy_depth,
            simulated_total_drift=total_drift,
            simulated_origin_distance=origin_distance,
            tau=tau,
            epsilon=epsilon,
        )
        cases.append(case)
    return cases


def rank_expression_cases(cases: list[ExpressionCase]) -> list[ExpressionCase]:
    """
    Rank expression cases by trust quality.

    Priority order:
    1) action quality: ACCEPT > FLAG > BLOCK
    2) lower total drift
    3) lower copy depth
    """
    action_priority = {
        "ACCEPT": 0,
        "FLAG": 1,
        "BLOCK": 2,
    }
    return sorted(
        cases,
        key=lambda case: (
            action_priority.get(case.action, 99),
            case.total_drift,
            case.copy_depth,
        ),
    )


def explain_expression_ranking(cases: list[ExpressionCase]) -> list[str]:
    """
    Explain why each ranked case outranks the next case below it.

    Input assumption:
    - cases are already ordered best-to-worst by current ranking rules.
    """
    action_priority = {
        "ACCEPT": 0,
        "FLAG": 1,
        "BLOCK": 2,
    }

    explanations: list[str] = []
    for i in range(len(cases) - 1):
        higher = cases[i]
        lower = cases[i + 1]

        higher_action_rank = action_priority.get(higher.action, 99)
        lower_action_rank = action_priority.get(lower.action, 99)

        # Primary rule: action class precedence.
        if higher_action_rank != lower_action_rank:
            explanations.append(
                f"{higher.name} outranks {lower.name} because "
                f"{higher.action} outranks {lower.action}."
            )
            continue

        # Secondary rule: lower total drift wins when action ties.
        if higher.total_drift != lower.total_drift:
            explanations.append(
                f"{higher.name} outranks {lower.name} because both are "
                f"{higher.action}, but {higher.name} has lower total drift."
            )
            continue

        # Tertiary rule: lower copy depth wins when action + drift tie.
        if higher.copy_depth != lower.copy_depth:
            explanations.append(
                f"{higher.name} outranks {lower.name} because both are "
                f"{higher.action} with equal drift, but {higher.name} has lower copy depth."
            )
            continue

        # Full tie under current ranking dimensions.
        explanations.append(
            f"{higher.name} and {lower.name} are tied under current ranking rules."
        )

    return explanations


# Canonical operator instances used by the demos and by any
# future experiments in this single-file lab. Keeping them as
# named constants makes intent explicit at call sites.
EQUALS = EqualsOperator(
    name="equals",
    glyph="=",
    description="Exact equivalence: both values must match exactly.",
)

APPROX = ApproxOperator(
    name="approx",
    glyph="≈",
    description="Approximate equivalence: values may differ within tolerance tau.",
)

DRIFT = DriftOperator(
    name="drift",
    glyph="Δ",
    description="Accumulated Xerox-style deviation across a transformation chain.",
)

NA = NaOperator(
    name="na_hold",
    glyph="Na",
    description="Hold state: do not resolve; require new evidence before proceeding.",
)

RESOLVE = ResolveOperator(
    name="resolve",
    glyph="R",
    description="Resolve state into action: ACCEPT, BLOCK, or FLAG.",
)


# =========================
# EDGE TESTING
# =========================


def edge_test(
    func: Callable[[float], float],
    test_values: List[float],
    expected_func: Callable[[float], float],
    tau: float,
) -> List[Tuple[float, float, float, str]]:
    """
    Push a rule or function to the edges.

    For each x:
        actual = func(x)
        expected = expected_func(x)
        compare them

    Returns tuples of:
        (x, actual, expected, PASS/FAIL)
    """
    results = []
    for x in test_values:
        actual = func(x)
        expected = expected_func(x)
        status = "PASS" if approx_equal(actual, expected, tau) else "FAIL"
        results.append((x, actual, expected, status))
    return results


def format_edge_results(results: List[Tuple[float, float, float, str]]) -> str:
    """Create a readable report for edge testing."""
    lines = []
    lines.append("=" * 60)
    lines.append("EDGE TEST REPORT")
    lines.append("=" * 60)
    for x, actual, expected, status in results:
        lines.append(
            f"x={x:8.3f} | actual={actual:10.4f} | "
            f"expected={expected:10.4f} | {status}"
        )
    return "\n".join(lines)


# =========================
# TOP STABILITY MODEL
# =========================


@dataclass
class TopModel:
    """
    Simple model of support distributed around center.

    The idea:
    - If support is balanced around center, the top is stable.
    - If one side dominates too much, the top wobbles.

    We use four directional supports just to keep the demo simple:
    left, right, up, down
    """
    left: float
    right: float
    up: float
    down: float

    def axis_balance_x(self) -> float:
        """How balanced is left vs right? Smaller is better."""
        return abs(self.left - self.right)

    def axis_balance_y(self) -> float:
        """How balanced is up vs down? Smaller is better."""
        return abs(self.up - self.down)

    def total_support(self) -> float:
        """Total support mass/weight in the system."""
        return self.left + self.right + self.up + self.down

    def wobble_score(self) -> float:
        """
        A simple wobble score.

        Lower = more stable.
        Higher = more wobble.
        """
        return self.axis_balance_x() + self.axis_balance_y()

    def state(self, wobble_tau: float = 1.0) -> str:
        """
        STABLE if wobble is within tolerance.
        WOBBLE if imbalance is too high.
        """
        return "WOBBLE" if self.wobble_score() > wobble_tau else "STABLE"

    def report(self, wobble_tau: float = 1.0) -> str:
        """Readable report for the top model."""
        lines = []
        lines.append("=" * 60)
        lines.append("TOP STABILITY REPORT")
        lines.append("=" * 60)
        lines.append(f"Left  support: {self.left}")
        lines.append(f"Right support: {self.right}")
        lines.append(f"Up    support: {self.up}")
        lines.append(f"Down  support: {self.down}")
        lines.append("")
        lines.append(f"X balance error: {self.axis_balance_x():.4f}")
        lines.append(f"Y balance error: {self.axis_balance_y():.4f}")
        lines.append(f"Wobble score:    {self.wobble_score():.4f}")
        lines.append(f"State:           {self.state(wobble_tau)}")
        return "\n".join(lines)


# =========================
# DEMOS
# =========================


def demo_drift_chain() -> None:
    """Demonstrate Xerox-style drift accumulating across steps."""
    chain = DriftChain(start_value=4.0, tau=1.0, epsilon=0.1)

    # These are intentionally slightly off to simulate repeated copying / drift.
    chain.add_step("copy_1", 4.10)
    chain.add_step("copy_2", 4.25)
    chain.add_step("copy_3", 4.55)
    chain.add_step("copy_4", 5.20)

    print(chain.report())

    # Show the same chain through the symbolic drift operator.
    # This is a compact machine-readable snapshot next to the
    # long human-readable chain report above.
    drift_summary = DRIFT.apply(chain)
    print("")
    print("DRIFT OPERATOR SNAPSHOT")
    print("-" * 60)
    for key, value in drift_summary.items():
        print(f"{key}: {value}")

    # Convert state into action using the minimal resolve operator.
    result = RESOLVE.apply(chain.state)
    print("")
    print("RESOLUTION REPORT")
    print("-----------------")
    print(f"state: {result['state']}")
    print(f"action: {result['action']}")
    print(f"reason: {result['reason']}")


def demo_drift_return_toward_origin() -> None:
    """
    Demonstrate path-length drift vs final origin distance.

    This case intentionally moves away and then returns near origin:
    - total_drift ends up relatively large
    - origin_distance ends up small
    """
    chain = DriftChain(start_value=4.0, tau=1.0, epsilon=0.1)
    chain.add_step("copy_1_away", 4.60)
    chain.add_step("copy_2_return", 4.20)
    chain.add_step("copy_3_near_origin", 4.05)

    print(chain.report())
    print("")
    print("DRIFT OPERATOR SNAPSHOT (RETURN TOWARD ORIGIN)")
    print("-" * 60)
    for key, value in DRIFT.apply(chain).items():
        print(f"{key}: {value}")

    # Same resolution pass for the return-toward-origin pattern.
    result = RESOLVE.apply(chain.state)
    print("")
    print("RESOLUTION REPORT")
    print("-----------------")
    print(f"state: {result['state']}")
    print(f"action: {result['action']}")
    print(f"reason: {result['reason']}")


def demo_edge_testing() -> None:
    """
    Demonstrate edge testing.

    We'll compare a correct rule to an intentionally weak approximation.
    """
    def correct_rule(x: float) -> float:
        return x * x

    def weak_rule(x: float) -> float:
        # Looks decent near the middle for some values,
        # but will fail harder at the edges.
        return 2 * x

    tests = [-10, -2, -1, 0, 1, 2, 10]
    tau = 0.5
    results = edge_test(weak_rule, tests, correct_rule, tau)
    print(format_edge_results(results))


def demo_top_model() -> None:
    """Demonstrate stable vs wobbling support around center."""
    stable_top = TopModel(left=5, right=5, up=4, down=4)
    wobble_top = TopModel(left=8, right=2, up=5, down=1)

    print(stable_top.report(wobble_tau=2.0))
    print()
    print(wobble_top.report(wobble_tau=2.0))


def demo_equality() -> None:
    """Show exact equality vs approximate equality."""
    a = 4.0
    b = 4.0
    c = 4.2
    tau = 0.25

    print("=" * 60)
    print("EQUALITY REPORT")
    print("=" * 60)
    print(f"EQUALS.apply({a}, {b}) -> {EQUALS.apply(a, b)}")
    print(f"EQUALS.apply({a}, {c}) -> {EQUALS.apply(a, c)}")
    print(f"APPROX.apply({a}, {c}, tau={tau}) -> {APPROX.apply(a, c, tau)}")


def demo_many_equations_equal_four() -> None:
    """
    Demonstrate that many expressions can compute to 4 while drift posture varies.

    The expression math result and the drift-path quality are reported together.
    """
    print("=" * 60)
    print("MANY EQUATIONS = 4 REPORT")
    print("=" * 60)

    cases = build_many_equations_equal_four_cases()

    for case in cases:
        print(f"name: {case.name}")
        print(f"expression: {case.expression}")
        print(f"computed_value: {case.computed_value}")
        print(f"expected_value: {case.expected_value}")
        print(f"copy_depth: {case.copy_depth}")
        print(f"total_drift: {case.total_drift}")
        print(f"origin_distance: {case.origin_distance}")
        print(f"state: {case.state}")
        print(f"action: {case.action}")
        print(f"caution_label: {case.caution_label}")
        print("")


def demo_expression_ranking() -> None:
    """
    Rank the same four expression cases by trust quality.

    This is a minimal comparison layer on top of existing case evaluation.
    """
    cases = build_many_equations_equal_four_cases()
    ranked_cases = rank_expression_cases(cases)

    print("=" * 60)
    print("EXPRESSION RANKING REPORT")
    print("=" * 60)
    for index, case in enumerate(ranked_cases, start=1):
        print(f"rank {index}:")
        print(f"name: {case.name}")
        print(f"action: {case.action}")
        print(f"total_drift: {case.total_drift}")
        print(f"copy_depth: {case.copy_depth}")
        print(f"caution_label: {case.caution_label}")
        print("")


def demo_expression_ranking_explanations() -> None:
    """
    Explain pairwise ranking decisions in plain English.
    """
    cases = build_many_equations_equal_four_cases()
    ranked_cases = rank_expression_cases(cases)
    explanations = explain_expression_ranking(ranked_cases)

    print("=" * 60)
    print("EXPRESSION RANKING EXPLANATIONS")
    print("=" * 60)
    for index, explanation in enumerate(explanations, start=1):
        print(f"{index}. {explanation}")


def demo_live_expression_batch() -> None:
    """
    Run a small live batch and rank by current trust heuristics.
    """
    expressions = [
        "2 + 2",
        "3.999 + 0.001",
        "(4.6 - 0.6)",
        "4.2",
        "8 / 2",
        "16 ** 0.5",
    ]
    ranked_cases = rank_expression_cases(run_expression_batch(expressions))

    print("=" * 60)
    print("LIVE EXPRESSION BATCH REPORT")
    print("=" * 60)
    for case in ranked_cases:
        print(f"expression: {case.expression}")
        print(f"computed_value: {case.computed_value}")
        print(f"copy_depth: {case.copy_depth}")
        print(f"total_drift: {case.total_drift}")
        print(f"origin_distance: {case.origin_distance}")
        print(f"state: {case.state}")
        print(f"action: {case.action}")
        print(f"caution_label: {case.caution_label}")
        print("")


def demo_na_operator() -> None:
    """
    Demonstrate explicit Na/HOLD operator output.

    This keeps the HOLD concept first-class and inspectable.
    """
    print("=" * 60)
    print("NA OPERATOR REPORT")
    print("=" * 60)
    result = NA.apply("drift exceeded threshold")
    print(result)


def format_qd_console_message(case: ExpressionCase) -> str:
    """
    Build a short QD-voice sentence from an evaluated case.
    """
    if case.action == "ACCEPT" and case.caution_label == "CLEAN":
        return "QD: Accept. Result matches target cleanly."
    if case.action == "ACCEPT" and case.caution_label == "CAUTION":
        return (
            "QD: Accept, but with caution. Result matches target, "
            "though the path looks structurally suspicious."
        )
    if case.action == "FLAG":
        return "QD: Flag. The result may match, but the path is unstable."
    if case.action == "BLOCK":
        return "QD: Block. The result does not safely meet the target."
    return "QD: Unable to classify this result cleanly."


def run_qd_console() -> None:
    """
    Minimal interactive console for one-expression-at-a-time QD checks.

    This is intentionally thin:
    - uses existing batch/evaluation logic
    - no custom parser
    - simple invalid-expression handling
    """
    print("QD CONSOLE")
    print("Type a math expression or 'exit' to quit.")
    while True:
        raw_expression = input("QD> ").strip()
        if raw_expression.lower() in {"exit", "quit"}:
            break
        try:
            case = run_expression_batch([raw_expression])[0]
        except Exception:
            print("invalid expression")
            continue

        print("----------------------------")
        print(f"expression: {case.expression}")
        print(f"computed_value: {case.computed_value}")
        print(f"total_drift: {case.total_drift}")
        print(f"state: {case.state}")
        print(f"action: {case.action}")
        print(f"caution: {case.caution_label}")
        print(format_qd_console_message(case))
        print("----------------------------")


# =========================
# MAIN
# =========================


if __name__ == "__main__":
    demo_equality()
    print("\n")
    demo_many_equations_equal_four()
    print("\n")
    demo_expression_ranking()
    print("\n")
    demo_expression_ranking_explanations()
    print("\n")
    demo_live_expression_batch()
    print("\n")
    demo_drift_chain()
    print("\n")
    demo_drift_return_toward_origin()
    print("\n")
    demo_na_operator()
    print("\n")
    demo_edge_testing()
    print("\n")
    demo_top_model()
    print("\n")
    run_qd_console()
