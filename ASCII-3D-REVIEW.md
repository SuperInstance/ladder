# Reviewing `ascii_3d_engine.py` — real code, three findings

The ExoJ line has now arrived at a 3D ASCII projection engine with a real file attached, so
this is a review of code rather than of a diagram. **The engine parses and the geometry is
right; three things are wrong, and one of them is the pattern this whole project keeps
hitting.**

---

## 1. All three rotation matrices are one axis off from their names

```python
R_yaw   = [[cy, -sy, 0], [sy,  cy, 0], [0, 0, 1]]   # this is a Z-axis (ROLL) matrix
R_pitch = [[cp, 0, sp],   [0, 1, 0], [-sp, 0, cp]]  # this is a Y-axis (YAW) matrix
R_roll  = [[1, 0, 0], [0, cr, -sr], [0, sr, cr]]     # this is an X-axis (ROLL) matrix
```

Measured, with a point on +X and one angle at a time:

| parameter passed | what actually moves | should be |
|---|---|---|
| `yaw=0.6` | X→Y — **spins in the screen plane** | about the vertical axis |
| `pitch=0.6` | X→Z — **rotates about the vertical** | about the horizontal axis |
| `roll=0.6` | X unchanged | correct for a roll axis |

The composition `R_yaw @ R_pitch @ R_roll` is therefore actually **Z @ Y @ X**, which *is* a
valid Tait–Bryan yaw-pitch-roll sequence. **The maths is fine. The names are shifted.**

That is worse than a maths error in one specific way: **the renderer's output looks correct
for every input**, so nothing crashes and nothing looks broken. But anyone tuning the view
will turn the wrong dial — pass `yaw` to look left and the hull rolls in place, pass `pitch`
to look up and it yaws. You get a plausible picture of the wrong rotation for as long as you
keep tuning.

The fix is renaming three variables. The alternative — rewriting the matrices so the names
match — is the same edit and is arguably the better one, because a caller who has already
tuned against the current behaviour keeps it.

```python
# either rename the variables...
R_roll_about_z, R_yaw_about_y, R_roll_about_x = ...
# ...or swap the matrices so the names are true
R_yaw   = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]   # about Y
R_pitch = [[1, 0, 0], [0, cp, -sp], [0, sp, cp]]   # about X
R_roll  = [[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]]   # about Z
```

I recommend the second, and then a three-line test that the axes are what they claim:

```python
R = renderer.create_rotation_matrices(yaw=np.pi/2, pitch=0, roll=0)
assert np.allclose(R @ [0,0,1], [1,0,0], atol=1e-9)   # yaw takes +Z to +X
```

**A rotation helper whose failure mode is "looks right" is the worst kind of bug, and it is
three lines to close.**

## 2. The depth buffer is written and then never read

This is the important one, and it is the same failure mode as the linter that flags everything
and the control that cannot fail: **a protection mechanism that exists, runs, and is bypassed.**

```python
if z_depth < z_buffer[py, px]:          # vertex pass — depth IS consulted
    z_buffer[py, px] = z_depth
    screen[py, px] = "█"
...
while True:
    if 0 <= x0 < self.width and 0 <= y0 < self.height:
        screen[y0, x0] = char_token      # edge pass — depth is NEVER consulted
```

Measured directly: the edge loop contains **no reference to `z_buffer` at all.** An edge at
depth 50 will paint over a vertex at depth 3, and the vertex you carefully depth-sorted will
be gone. The comment is honest about it — *"Line overlay without depth sorting for wireframe
integrity grids"* — which is a decision, not an accident, but it means **`z_buffer` is doing
nothing for the case it looks like it is doing something for.**

Either the edges get a depth and honour the buffer:

```python
if z_depth_interp < z_buffer[y0, x0]:
    z_buffer[y0, x0] = z_depth_interp
    screen[y0, x0] = char_token
```

or the buffer is deleted and the class stops claiming depth-sorted vertices, so the next
reader does not extend the wrong belief. **A dead control is worse than no control, because
it is trusted.**

## 3. `dtype=object` for a screen buffer, on a path that claims high performance

```python
screen = np.full((self.height, self.width), " ", dtype=object)
```

Every cell is a **Python object reference to a one-character string**. numpy's native Unicode
dtype is `<U1` — one codepoint per cell, no boxing, and `"".join` on a `<U1` row is a
contiguous read. For an 80×35 buffer it is not slow, so this is not a performance bug *yet*;
it becomes one the moment the buffer is large or the render is called at a display rate, and
it is the kind of thing that gets discovered late.

```python
screen = np.full((self.height, self.width), " ", dtype="<U1")
```

One character, and the whole thing becomes vectorisable.

## 4. A smaller one, and the fix is a length check

```python
char_token = "▒" if shading_intensities is None else self.palette[
    min(len(self.palette) - 1, int(shading_intensities[edge_idx] * ...))]
```

`shading_intensities` is indexed by `edge_idx` with no check that it is as long as `edges`. A
mismatch raises `IndexError` in the middle of a Bresenham loop, after the screen is half
written. Cheap, and the kind of thing that shows up as an intermittent render glitch on a
live display rather than as a clean error.

## Verdict

The geometry, the projection, the z-clip and the line rasteriser are all correct. **This is
good code with three mislabelled things in it**, and the worst of the three is a depth buffer
that is maintained and ignored.

Findings 1 and 2 are worth ten minutes each. Finding 1 in particular will cost someone an
afternoon of tuning a renderer that is working exactly as written and not as documented.
