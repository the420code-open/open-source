"""AP02's results at their own formulas, as the world's specification, Part Six, gives them.

Zero-Clause BSD.
"""
import math


def drift(a, E0, t):
    """Theorem I.1: with no input, the stock decays as E0 * e^(-a t)."""
    return E0 * math.exp(-a * t)


def least_cost_point(a, lam):
    """Theorem II.1: the least-cost point x = 1 / (1 + lam a^2)."""
    return 1.0 / (1.0 + lam * a * a)


def least_cost_effort(a, lam):
    """Theorem II.1: the effort that holds it, u = a / (1 + lam a^2)."""
    return a / (1.0 + lam * a * a)


def event_horizon(a, u_max):
    """Theorem III.1: x_H = u_max / a. Above it, the stock falls even at full effort."""
    return u_max / a


def mean_effort_cost(lam, schedule):
    """Theorem IV.1: the mean cost of effort, lam u^2, over a repeating schedule of efforts."""
    return sum(lam * u * u for u in schedule) / len(schedule)


def coupled_steady_state(a1, a2, lam, k):
    """Theorem VI.1: two operators, each at its own least-cost effort, joined by a passive link k.

    Solves -a1 E1 + u1 + k (E2 - E1) = 0 and -a2 E2 + u2 + k (E1 - E2) = 0.
    Returns u1, u2, E1, E2 and the standing flow k (E1 - E2), from operator 1 to operator 2.
    """
    u1, u2 = least_cost_effort(a1, lam), least_cost_effort(a2, lam)
    det = (a1 + k) * (a2 + k) - k * k
    E1 = ((a2 + k) * u1 + k * u2) / det
    E2 = ((a1 + k) * u2 + k * u1) / det
    return {"u1": u1, "u2": u2, "E1": E1, "E2": E2, "flow": k * (E1 - E2)}


def evaluate(name, inputs, output):
    if name == "drift":
        return drift(inputs["a"], inputs["E0"], inputs["t"])
    if name == "least_cost_point":
        return least_cost_point(inputs["a"], inputs["lam"])
    if name == "least_cost_effort":
        return least_cost_effort(inputs["a"], inputs["lam"])
    if name == "event_horizon":
        return event_horizon(inputs["a"], inputs["u_max"])
    if name == "mean_effort_cost":
        return mean_effort_cost(inputs["lam"], inputs["schedule"])
    if name == "coupled_steady_state":
        return coupled_steady_state(inputs["a1"], inputs["a2"], inputs["lam"], inputs["k"])[output]
    raise KeyError(name)
