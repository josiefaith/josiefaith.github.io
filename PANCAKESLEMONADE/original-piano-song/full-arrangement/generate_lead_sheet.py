#!/usr/bin/env python3
"""Build lead_sheet.html: the chord chart by bar number, read from ../generate_piano_song.py."""
import ast
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'generate_piano_song.py')
ns = {}
for node in ast.parse(open(SRC).read()).body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in
            {'VERSE', 'PRE_1', 'PRE_2', 'CHORUS_A', 'CHORUS_B', 'BRIDGE', 'OUTRO', 'FORM'}
            for t in node.targets):
        exec(compile(ast.Module([node], []), 'src', 'exec'), ns)

# performance cues by bar (what the band does, where the singer breathes)
CUES = {
    1: 'piano hook', 3: 'drums enter', 8: 'piano answers', 12: 'piano answers',
    16: 'band stops on 4', 24: 'piano answer phrase', 25: 'hook returns',
    30: 'piano answers', 34: 'piano answers', 38: 'tom fill', 46: 'fill',
    47: 'half-time', 51: 'build', 55: 'drop out', 56: 'build',
    64: 'piano answer phrase', 65: 'pull back', 68: 'fill', 69: 'full band',
    72: 'piano answer phrase', 73: 'hook', 79: 'rit.', 80: 'hold',
}
NOTES = {
    'Bridge': 'Key change: G♭ major',
    'Breakdown': 'Back toward E♭',
    'Final Chorus (pull-back + lift)': 'Bars 65–68 quiet, 69–72 loudest',
}


def acc(s):
    return s.replace('b', '♭').replace('#', '♯')


def chord_html(name):
    m = re.fullmatch(r'([A-G]b?)(m(?!aj))?([^/]*)(?:/([A-G]b?))?', name)
    root, minor, ext, bass = m.groups()
    out = f'<span class="rt">{acc(root)}{"m" if minor else ""}</span>'
    if ext:
        out += f'<sup>{acc(ext)}</sup>'
    if bass:
        out += f'<span class="sl">/{acc(bass)}</span>'
    return f'<span class="ch">{out}</span>'


sections, bar = [], 1
for name, style, chords, *_ in ns['FORM']:
    sections.append((name, bar, chords))
    bar += len(chords)
TOTAL = bar - 1

form_strip = ''.join(
    f'<li><span class="fs-name">{html.escape(n.replace(" (pull-back + lift)", " II"))}</span>'
    f'<span class="fs-bars">{s}–{s + len(c) - 1}</span></li>' for n, s, c in sections)

blocks = []
for name, start, chords in sections:
    cells = []
    for i, bc in enumerate(chords):
        b = start + i
        cue = CUES.get(b, '')
        last = b == TOTAL
        cells.append(
            f'<div class="bar{" two" if len(bc) == 2 else ""}{" end" if last else ""}">'
            f'<span class="bn">{b}</span>'
            f'<div class="chords">{"".join(chord_html(c) for c in bc)}</div>'
            f'{f"<span class=cue>{cue}</span>" if cue else ""}</div>')
    note = NOTES.get(name, '')
    blocks.append(
        f'<section class="sec"><header><h2>{html.escape(name)}</h2>'
        f'<span class="range">bars {start}–{start + len(chords) - 1}</span>'
        f'{f"<span class=note>{note}</span>" if note else ""}</header>'
        f'<div class="grid">{"".join(cells)}</div></section>')

page = f'''<title>Untitled in E♭</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Lora:ital,wght@0,400;0,600;1,400&family=Reenie+Beanie&display=swap">
<style>
/* Layout: a printed chart. Four bars to a line, barlines between bars, section names as rehearsal marks. */
:root {{
  --paper: #fbf8f2; --ink: #2a2140; --muted: #6f6582; --rule: #cfc6dc;
  --accent: #8a5a12; --mark: #efe6f7;
  --display: "Playfair Display", Georgia, serif;
  --body: "Lora", Georgia, serif;
  --hand: "Reenie Beanie", "Bradley Hand", cursive;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #1b1529; --ink: #efe8f8; --muted: #a99dbd; --rule: #3e3456;
  --accent: #e8b25c; --mark: #2a2140; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --paper: #1b1529; --ink: #efe8f8; --muted: #a99dbd; --rule: #3e3456;
  --accent: #e8b25c; --mark: #2a2140; color-scheme: dark; }}
body {{ background: var(--paper); color: var(--ink); font-family: var(--body); }}
.sheet {{ max-width: 920px; margin: 0 auto; padding-inline: 20px; padding-block: 32px 48px; }}
.top {{ display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 12px 24px;
  border-bottom: 2px solid var(--ink); padding-bottom: 14px; }}
.eyebrow {{ font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin: 0 0 4px; }}
h1 {{ font-family: var(--display); font-weight: 700; font-size: clamp(30px, 6vw, 44px); line-height: 1.05; margin: 0; text-wrap: balance; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 0; font-size: 14px; }}
.meta div {{ display: flex; flex-direction: column; }}
.meta dt {{ font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }}
.meta dd {{ margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; }}
.form {{ list-style: none; display: flex; flex-wrap: wrap; gap: 6px; padding: 0; margin: 16px 0 6px; }}
.form li {{ display: flex; gap: 6px; align-items: baseline; padding: 3px 9px; border: 1px solid var(--rule); border-radius: 999px; font-size: 12.5px; }}
.fs-bars {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
.howto {{ font-size: 13px; color: var(--muted); margin: 8px 0 0; }}
.sec {{ margin-top: 26px; break-inside: avoid; }}
.sec header {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; margin-bottom: 8px; }}
h2 {{ font-family: var(--display); font-weight: 500; font-size: 21px; margin: 0; padding: 1px 10px; background: var(--mark); border-radius: 4px; }}
.range {{ font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.note {{ font-size: 13px; font-style: italic; color: var(--accent); }}
.grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-left: 2px solid var(--ink); }}
.bar {{ position: relative; min-height: 78px; padding: 18px 10px 18px; border-right: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule); display: flex; align-items: center; }}
.bar.end {{ border-right: 5px double var(--ink); }}
.bn {{ position: absolute; top: 4px; left: 7px; font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.chords {{ display: flex; width: 100%; justify-content: space-between; gap: 6px; min-width: 0; }}
.ch {{ font-family: var(--body); font-weight: 600; font-size: 22px; white-space: nowrap; color: var(--ink); }}
.ch sup {{ font-size: .58em; font-weight: 600; margin-left: 1px; }}
.ch .sl {{ font-size: .8em; color: var(--muted); }}
.two .ch {{ font-size: 19px; }}
.cue {{ position: absolute; bottom: 1px; right: 8px; font-family: var(--hand); font-size: 19px; line-height: 1; color: var(--accent); }}
.legend {{ margin-top: 30px; font-size: 13px; color: var(--muted); border-top: 1px solid var(--rule); padding-top: 12px; }}
.legend p {{ margin: 4px 0; max-width: 70ch; }}
@media (max-width: 620px) {{
  .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .ch {{ font-size: 20px; }} .two .ch {{ font-size: 17px; }}
}}
@media print {{
  :root {{ --paper: #fff; --ink: #000; --muted: #555; --rule: #bbb; --accent: #444; --mark: #eee; }}
  .sheet {{ padding-block: 0; }} .sec {{ margin-top: 14px; }} .bar {{ min-height: 60px; }}
}}
</style>
<main class="sheet">
  <div class="top">
    <div><p class="eyebrow">Lead sheet · chords by bar</p><h1>Untitled in E♭</h1></div>
    <dl class="meta">
      <div><dt>Key</dt><dd>E♭ major</dd></div>
      <div><dt>Tempo</dt><dd>♩ = 96</dd></div>
      <div><dt>Meter</dt><dd>4/4</dd></div>
      <div><dt>Length</dt><dd>{TOTAL} bars · 3:20</dd></div>
    </dl>
  </div>
  <ol class="form" aria-label="Form">{form_strip}</ol>
  <p class="howto">One box is one bar. Two chords in a box split the bar: the second chord lands on beat 3.</p>
  {"".join(blocks)}
  <div class="legend">
    <p><strong>Feel:</strong> mid-tempo, straight 16ths. The piano plays a short hook in bars 1–4 that comes back in bars 25, 55 and 73.</p>
    <p><strong>Notes in orange:</strong> where the piano answers the vocal (good places to breathe), where the band stops, fills, or pulls back. The tempo slows over bars 79–80.</p>
  </div>
</main>
'''
open(os.path.join(HERE, 'lead_sheet.html'), 'w').write(page)
print('wrote lead_sheet.html,', TOTAL, 'bars')
