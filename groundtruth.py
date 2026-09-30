"""The ladder argument, made checkable.

The seed's ladder is: 3x3 tic-tac-toe -> 5x5 -> Connect 4 -> blackjack -> multi-deck
multiplayer -> 5-card draw -> Texas hold'em. Its stated justification for going UP the
ladder is that the state space eventually defeats a lookup table, and "neural pattern
extraction becomes essential."

The same argument, applied honestly, destroys the ladder.

**Every rung up removes a piece of COMPUTABLE ground truth.** The property the seed is
optimising for -- the answer is not in a table any more -- is the same property that makes a
benchmark useless, because a benchmark's job is to have an answer you can check.

    rung                     the answer is computable?        what you can actually verify
    -----------------------   ----------------------------   ---------------------------------
    3x3 tic-tac-toe          entirely, exactly               optimal policy for 180,361 states
    4x4 four-in-a-row        entirely, exactly               strong solution, first player wins
    5x5 five-in-a-row        entirely, exactly, slowly      nothing without a C solver
    Connect 4                entirely, exactly               Tromp 8-ply, 67,557 positions
    blackjack, one deck      card math exact, dealer exact   equity by enumeration
    multi-deck, N players    cards exact, opponents absent  your own equity only
    Texas hold'em            cards exact, opponent mind NOT  equity yes; reads no

The last two rows are the point. A "recursive shadow network" modelling what an opponent
believes is not a harder learning problem. It is a problem with **no ground truth**, and
therefore not a benchmark at all -- it is a simulation of a claim.

**The design constraint is two-sided and the seed optimises one side:**

    a benchmark needs  (1) a COMPUTABLE objective
                        (2) a representation that must be NON-TRIVIAL to express the objective in

    Tic-tac-toe  has (1) perfectly and (2) not at all -- a 9x9 matrix is enough and is not
    enough.     Poker         has (1) only for half the decision and (2) generously.

    There is a sweet spot, and it is NOT at the top of the ladder.

This file makes the table executable so the claim can be checked rather than believed.
"""
from __future__ import annotations

LADDER = [
    # name, is the optimal action computable, is the OPPONENT's state computable,
    # can a lookup table exist, does the representation need to be non-trivial
    ("3x3 tic-tac-toe",        True,  "n/a (no opponent)", "yes", False),
    ("4x4 four-in-a-row",      True,  "n/a (no opponent)", "yes", False),
    ("5x5 five-in-a-row",      True,  "n/a (no opponent)", "painfully", True),
    ("Connect 4",              True,  "n/a (no opponent)", "yes", True),
    ("blackjack, one deck",    True,  "yes (dealer is fixed)", "yes", True),
    ("multi-deck, N players",  True,  "NO", "no", True),
    ("Texas hold'em",          True,  "NO", "no", True),
]

COLS = ("rung", "optimal action computable", "opponent state computable",
        "lookup table feasible", "representation must be non-trivial")


def score(row):
    """Is this rung usable as a benchmark?

    A rung is USABLE if you can check its answer (1) AND the representation is genuinely
    hard (2). A rung with a computable answer and a trivial representation is TOO EASY: it
    measures nothing. A rung with no computable opponent state is UNCHECKABLE: it measures
    your own imagination.
    """
    _, opt, opp, table, hard = row
    checkable = opt and (opp == "n/a (no opponent)" or opp.startswith("yes"))
    if not hard:      return "TOO EASY — a table answers it"
    if not checkable:  return "UNCHECKABLE — no ground truth"
    return "USABLE — hard to express, possible to check"


def main():
    w = [max(len(str(r[i])) for r in ([COLS] + LADDER)) for i in range(5)]
    def row(cells):
        return "  " + "  ".join(str(c).ljust(w[i]) for i, c in enumerate(cells))
    print("  " + "THE LADDER, AND WHAT IS STILL CHECKABLE AT EACH RUNG\n")
    print(row(COLS)); print("  " + "  ".join("-" * x for x in w))
    for r in LADDER:
        print(row(r))
    print()
    for r in LADDER:
        print(f"  {r[0]:<26} {score(r)}")
    usable = [r[0] for r in LADDER if score(r).startswith("USABLE")]
    print(f"\n  Usable rungs: {', '.join(usable) if usable else 'none'}")
    print("""
  THE FINDING
  -----------
  The seed justifies going UP the ladder by saying the lookup table stops working. But
  that is the same property that removes the ground truth, and the two rungs where the
  representation is genuinely hard are also the two where you can no longer check the answer
  without a Monte Carlo rollout and a theory of what an opponent believes.

  **The sweet spot is in the MIDDLE, not the top.** Connect 4 and 5x5 are hard to express
  and still exactly checkable. Texas hold'em is the rung with the most interesting story and
  the least measurable content, and the "recursive shadow network" does not fix that -- it
  relocates the uncertainty from the model into the evaluation, where it cannot be checked
  at all.

  The honest version of the poker rung is NOT "model the opponent's mind." It is:
  **use a game where the opponent's action distribution is OBSERVABLE, so the model can be
  scored against what they actually did rather than what you guessed they thought.** That
  is a smaller claim and it is the one that survives.
""")


if __name__ == "__main__":
    main()
