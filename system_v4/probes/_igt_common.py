"""Common scaffolding for IGT atom sims.

IGT (Infinite Game Theory) encodes a nested yin/yang structure:
- Inner axis: win (+1) vs lose (-1)   -- short-term, finite-game payoff
- Outer axis: WIN (+1) vs LOSE (-1)   -- long-term, infinite-game payoff

A player state is a pair (inner, outer) in {-1,+1}^2, giving 4 carriers:
  (+1, +1)  win  & WIN   -- aligned virtuous
  (+1, -1)  win  & LOSE  -- pyrrhic / short-term greed
  (-1, +1)  lose & WIN   -- sacrifice / long-term investment
  (-1, -1)  lose & LOSE  -- doomed

Chirality: the cyclic rotation (win,WIN)->(win,LOSE)->(lose,LOSE)->(lose,WIN)
is CW; its reverse is CCW.  These two orientations are the IGT yin/yang
spinors.
"""
import numpy as np

CARRIERS = [
    ( 1,  1),  # win WIN
    ( 1, -1),  # win LOSE
    (-1, -1),  # lose LOSE
    (-1,  1),  # lose WIN
]

LABELS = {
    ( 1,  1): "win_WIN",
    ( 1, -1): "win_LOSE",
    (-1, -1): "lose_LOSE",
    (-1,  1): "lose_WIN",
}


def carrier_index(s):
    return CARRIERS.index(tuple(s))


def reduce_outer(state):
    """Project short-term-only view: forget outer axis."""
    return state[0]


def reduce_inner(state):
    """Project long-term-only view: forget inner axis."""
    return state[1]


def distinguishable(a, b, probe="full"):
    if probe == "full":
        return a != b
    if probe == "inner":
        return a[0] != b[0]
    if probe == "outer":
        return a[1] != b[1]
    raise ValueError(probe)


def cw_next(state):
    """CW rotation around the 4-carrier ring."""
    i = CARRIERS.index(tuple(state))
    return CARRIERS[(i + 1) % 4]


def ccw_next(state):
    i = CARRIERS.index(tuple(state))
    return CARRIERS[(i - 1) % 4]
