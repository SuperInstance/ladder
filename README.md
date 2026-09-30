# ladder

An adversarial reading of two seeded architectures for the training ladder: a poker "J-space
Theory-of-Mind" system, and a shared-memory "power-armor" grid.

- `groundtruth.py` — the ladder scored for **what is still checkable at each rung**. Prints a
  table and classifies every rung as TOO EASY, UNCHECKABLE, or USABLE. No arguments; run it.
- `FINDINGS.md` — the analysis. The ladder's own justification defeats the ladder; the
  memory layout does not filter, it hides; and the fix is a sequence number.

## The short version

| claim from the seeds | verdict |
|---|---|
| climb the ladder because the lookup table stops working | **self-defeating** — that is the same property that removes the ground truth |
| poker's difficulty is the opponent's mind, so build a ToM vector | the decomposition is right, the **target is not checkable** — use an observable action distribution instead |
| a shared memory-mapped grid is zero-copy and fast | **true and worth doing** |
| the layout "acts as a hard filter" on noise | **false** — a dropped frame arrives as a stale value that looks current |
| — | the fix is a producer sequence number, which is also what makes the data auditable |

The usable rungs are **5x5, Connect 4, and single-deck blackjack**. The sweet spot is in the
middle of the ladder, not the top.
