#!/usr/bin/env python3
"""Build lead_sheet.html for Pancakes and Lemonade: chords by bar (from generate_piano.py) with lyrics."""
import ast
import html
import os
import re

import chord_shapes as cs

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'generate_piano.py')
ns = {}
for node in ast.parse(open(SRC).read()).body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in
            {'VERSE', 'PRE_1', 'PRE_2', 'CHORUS_A', 'CHORUS_B', 'BRIDGE', 'OUTRO', 'FORM'}
            for t in node.targets):
        exec(compile(ast.Module([node], []), 'src', 'exec'), ns)

# performance cues by bar (what the band does, where the singer breathes)
CUES = {
    1: 'piano hook', 3: 'drums enter', 24: 'band stops on 4', 25: 'light',
    33: 'piano hook', 35: 'shaker', 46: 'tom fill', 47: 'full band',
    54: 'fill', 55: 'half-time', 59: 'build', 63: 'drop out', 64: 'build', 65: 'biggest',
    73: 'pull back', 76: 'fill', 77: 'full band', 87: 'rit.', 88: 'hold',
}

# Lyrics by bar, placed from josie's chord sheet. A pair splits a two-chord bar (second half = beat 3).
VERSE_1 = ['Dawn comes', "the stove\u2019s on", 'pancakes and lemonade', 'sweet syrup of your toothpaste',
           'and I am', ('fortunate to be', 'breathing'), 'look how the', ('sun is', 'shining')]
CHORUS_1 = ['I got time on my side', 'and a skip in my stride', 'and you know what they say',
            'money comes back', 'but time doesn\u2019t wait', 'for a beautiful face',
            ('stop being', 'so fake'), ('i\u2019m just', 'doing my thing today')]
CHORUS_2 = ['I\u2019ve got time on my side', 'and a swing in my stride', 'and you know what they say',
            'money comes back', 'but time it\u2019s as chaste', 'as a lover\u2019s embrace',
            ('and you know', 'you can\u2019t stay'), ('this young so I\u2019ll', 'do my thing today')]
LYRICS = {}
for start, lines in [
    (5, VERSE_1),
    (13, ['shoes on', 'autumn air', 'just a black coffee please', 'or maybe an Earl Grey tea', 'so',
          ('I can start my day all warm', 'inside'), 'so happy', ('to be', 'alive')]),
    (21, ['Debit card is in my wallet', ('no money\u2019s', 'on it'), ('but that\u2019s', 'not gonna'),
          ('faze me', 'cuz')]),
    (25, CHORUS_1),
    (35, ['I get off', 'at York Street', 'I walk down the promenade', 'East River is rushing on',
          'and I will', ('lose myself in the sea', 'the sea'), 'of visiting', ('camera', 'flashes')]),
    (43, ['buy another coffee', ('cuz who needs', 'money'), ('but I', 'sure need the'), ('caffeine', 'cuz')]),
    (47, CHORUS_2),
    (55, ['(vocalize \u201ctoday\u201d)']),
    (63, ['(rest)', ('look how the sun is', 'shining')]),
    (65, CHORUS_1[:7] + [('i\u2019m just', 'doing my thing')]),
    (73, CHORUS_2),
    (81, VERSE_1[:4] + ['and I am', 'fortunate to be', 'breathing']),
]:
    for k, line in enumerate(lines):
        LYRICS[start + k] = line
NOTES = {
    'Chorus 1': 'Held chords, softer drums: the big chorus waits',
    'Bridge': 'Key change: G♭ major',
    'Breakdown': 'Back toward E♭',
    'Final Chorus (pull-back + lift)': 'Bars 73–76 quiet, 77–80 loudest',
}


def acc(s):
    return s.replace('b', '♭').replace('#', '♯')


def slug(name):
    return 'c-' + re.sub(r'[^A-Za-z0-9]+', '-', name.replace('#', 's')).strip('-')


def chord_html(name, link=True):
    m = re.fullmatch(r'([A-G]b?)(m(?!aj))?([^/]*)(?:/([A-G]b?))?', name)
    root, minor, ext, bass = m.groups()
    out = f'<span class="rt">{acc(root)}{"m" if minor else ""}</span>'
    if ext:
        out += f'<sup>{acc(ext)}</sup>'
    if bass:
        out += f'<span class="sl">/{acc(bass)}</span>'
    if link:
        return f'<a class="ch" href="#{slug(name)}">{out}</a>'
    return f'<span class="ch">{out}</span>'


sections, bar = [], 1
for name, style, chords, *_ in ns['FORM']:
    sections.append((name, bar, chords))
    bar += len(chords)
TOTAL = bar - 1

form_strip = ''.join(
    f'<li><span class="fs-name">{html.escape(n.replace(" (pull-back + lift)", " II"))}</span>'
    f'<span class="fs-bars">{s}–{s + len(c) - 1}</span></li>' for n, s, c in sections)

VOICINGS = cs.piano_voicings()
blocks = []
for name, start, chords in sections:
    cells = []
    for i, bc in enumerate(chords):
        b = start + i
        cue = CUES.get(b, '')
        last = b == TOTAL
        lyr = LYRICS.get(b, '')
        lyr = list(lyr) if isinstance(lyr, tuple) else [lyr] + [''] * (len(bc) - 1)
        cols = ''.join(f'<div class="col">{chord_html(c)}{cs.piano_svg(*VOICINGS[c], c)}'
                       f'<span class="ly">{html.escape(l)}</span></div>'
                       for c, l in zip(bc, lyr))
        cells.append(
            f'<div class="bar{" two" if len(bc) == 2 else ""}{" end" if last else ""}">'
            f'<span class="bn">{b}</span>'
            f'<div class="chords">{cols}</div>'
            f'{f"<span class=cue>{cue}</span>" if cue else ""}</div>')
    note = NOTES.get(name, '')
    blocks.append(
        f'<section class="sec"><header><h2>{html.escape(name)}</h2>'
        f'<span class="range">bars {start}–{start + len(chords) - 1}</span>'
        f'{f"<span class=note>{note}</span>" if note else ""}</header>'
        f'<div class="grid">{"".join(cells)}</div></section>')

# ---------- chord shapes ----------
CAPO, SHAPES, _ = cs.guitar_shapes(list(VOICINGS))
DROPS = {'maj9': 'the 9th', 'm9': 'the 9th', '9': 'the 9th', '9sus4': 'the 9th', 'm11': 'the 11th',
         '13': 'the 13th', '7b9': 'the ♭9', 'maj7#11': 'the ♯11'}
cards = []
for name, (lh, rh) in VOICINGS.items():
    (score, combo, barre), easy = SHAPES[name]
    qual = cs.parse(name)[1]
    lh_txt = ' '.join(cs.with_octave(p, name) for p in lh)
    rh_txt = ' '.join(cs.with_octave(p, name) for p in rh)
    simp = (f'<span class="simp">Easier version: leaves out {DROPS[qual]}</span>'
            if easy and qual in DROPS else '')
    cards.append(
        f'<article class="card" id="{slug(name)}"><h3>{chord_html(name, link=False)}</h3>'
        f'<div class="pn">{cs.piano_svg(lh, rh, name)}'
        f'<p class="vn"><span class="tag t-lh">LH</span> {lh_txt}'
        f' <span class="tag t-rh">RH</span> {rh_txt}</p></div>'
        f'<div class="gt">{cs.guitar_svg(combo, barre, name)}'
        f'<p><span class="shape">{cs.shape_name(name, CAPO, easy)}</span> shape'
        f'{f" · capo {CAPO}" if CAPO else ""}<br>{simp}'
        f'<span class="snd">Sounds: {cs.sounding_notes(combo, CAPO, name)}</span></p></div></article>')
shapes_html = f'''<section class="shapes" id="chords">
    <h2 class="sh">How to play the chords</h2>
    <p class="howto">Every chord in the song, in the order it first appears. Tap a chord in the chart above to jump here.</p>
    <p class="howto"><strong>Piano:</strong> the voicing the piano in the track plays most often.
      <span class="tag t-lh">LH</span> left hand, <span class="tag t-rh">RH</span> right hand. The dot under
      the keyboard marks middle C (C4). Numbers on the keys are suggested fingers: 1 = thumb, 5 = pinky,
      in both hands. The same keyboard appears under each chord in the chart.</p>
    <p class="howto"><strong>Guitar:</strong> the easiest shape the search found for each chord, all with a
      <strong>capo on fret {CAPO}</strong>. The shape name is what your fingers make with the capo on. × means
      don't play that string; ○ means play it open. Numbers in the dots are fretting fingers:
      1 = index, 2 = middle, 3 = ring, 4 = pinky. Shapes marked "easier version" leave out one colour note,
      which the piano still plays.</p>
    <div class="cards">{"".join(cards)}</div>
  </section>'''

page = f'''<title>Pancakes and Lemonade</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Lora:ital,wght@0,400;0,600;1,400&family=Reenie+Beanie&display=swap">
<style>
/* Layout: a printed chart. Four bars to a line, barlines between bars, section names as rehearsal marks. */
:root {{
  --paper: #fbf8f2; --ink: #2a2140; --muted: #6f6582; --rule: #cfc6dc;
  --accent: #8a5a12; --mark: #efe6f7;
  --key: #ffffff; --keyline: #8d84a0; --keyblack: #2a2140; --lh: #d39a2c; --rh: #7a5cc4;
  --fn-lh: #2a2140; --fn-rh: #ffffff;
  --display: "Playfair Display", Georgia, serif;
  --body: "Lora", Georgia, serif;
  --hand: "Reenie Beanie", "Bradley Hand", cursive;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #1b1529; --ink: #efe8f8; --muted: #a99dbd; --rule: #3e3456;
  --accent: #e8b25c; --mark: #2a2140; color-scheme: dark;
  --key: #e9e4f1; --keyline: #3e3456; --keyblack: #120d1d; --lh: #e8b25c; --rh: #a78bea;
  --fn-lh: #1b1529; --fn-rh: #1b1529; }} }}
:root[data-theme="dark"] {{
  --paper: #1b1529; --ink: #efe8f8; --muted: #a99dbd; --rule: #3e3456;
  --accent: #e8b25c; --mark: #2a2140; color-scheme: dark;
  --key: #e9e4f1; --keyline: #3e3456; --keyblack: #120d1d; --lh: #e8b25c; --rh: #a78bea;
  --fn-lh: #1b1529; --fn-rh: #1b1529; }}
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
.bar {{ position: relative; min-height: 92px; padding: 20px 10px 12px; border-right: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule); display: flex; align-items: flex-start; }}
.bar.end {{ border-right: 5px double var(--ink); }}
.bn {{ position: absolute; top: 4px; left: 7px; font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.chords {{ display: flex; flex-wrap: wrap; width: 100%; gap: 10px 12px; min-width: 0; }}\n.col {{ flex: 1 1 150px; min-width: 0; display: flex; flex-direction: column; gap: 4px; }}\n.ly {{ font-style: italic; font-size: 14px; line-height: 1.3; color: var(--ink); overflow-wrap: anywhere; }}
.ch {{ font-family: var(--body); font-weight: 600; font-size: 22px; white-space: nowrap; color: var(--ink); }}
.ch sup {{ font-size: .58em; font-weight: 600; margin-left: 1px; }}
.ch .sl {{ font-size: .8em; color: var(--muted); }}
.two .ch {{ font-size: 19px; }}
.cue {{ position: absolute; top: 1px; right: 8px; font-family: var(--hand); font-size: 19px; line-height: 1; color: var(--accent); }}
.legend {{ margin-top: 30px; font-size: 13px; color: var(--muted); border-top: 1px solid var(--rule); padding-top: 12px; }}
.legend p {{ margin: 4px 0; max-width: 70ch; }}
.shapes {{ margin-top: 40px; border-top: 2px solid var(--ink); padding-top: 18px; }}
h2.sh {{ font-family: var(--display); font-weight: 700; font-size: 28px; margin: 0 0 8px; padding: 0; background: none; }}
.shapes .howto {{ max-width: 72ch; }}
a.ch {{ text-decoration: none; }}
a.ch:hover, a.ch:focus-visible {{ text-decoration: underline; text-decoration-color: var(--accent); }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; margin-top: 16px; }}
.card {{ border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; display: flex; flex-direction: column;
  gap: 10px; break-inside: avoid; scroll-margin-top: 16px; min-width: 0; }}
.card:target {{ border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }}
.card h3 {{ margin: 0; font-weight: 600; }}
.card h3 .ch {{ font-size: 24px; }}
.kb {{ width: 100%; height: auto; display: block; }}
.k-w {{ fill: var(--key); stroke: var(--keyline); stroke-width: .6; }}
.k-b {{ fill: var(--keyblack); }}
.k-lh {{ fill: var(--lh); stroke: var(--keyline); stroke-width: .6; }}
.k-rh {{ fill: var(--rh); stroke: var(--keyline); stroke-width: .6; }}
.k-mid {{ fill: var(--muted); }}
.kfn {{ font: 600 6.5px var(--body); text-anchor: middle; }}
.kfb {{ font-size: 5.5px; }}
.fn-lh {{ fill: var(--fn-lh); }} .fn-rh {{ fill: var(--fn-rh); }}
.g-fn {{ font: 700 6.5px var(--body); text-anchor: middle; fill: var(--paper); }}
.bar .kb {{ margin: 2px 0 2px; }}
.vn {{ margin: 6px 0 0; font-size: 13.5px; line-height: 1.6; font-variant-numeric: tabular-nums; }}
.tag {{ display: inline-block; font-size: 10.5px; font-weight: 600; letter-spacing: .06em; padding: 0 5px;
  border-radius: 3px; color: var(--paper); line-height: 1.5; }}
.t-lh {{ background: var(--lh); }} .t-rh {{ background: var(--rh); }}
.gt {{ display: flex; gap: 12px; align-items: flex-start; border-top: 1px dashed var(--rule); padding-top: 10px; }}
.gt p {{ margin: 0; font-size: 13.5px; line-height: 1.5; min-width: 0; }}
.gb {{ width: 92px; height: auto; flex: none; }}
.g-line {{ stroke: var(--muted); stroke-width: .8; }}
.g-nut {{ fill: var(--ink); }}
.g-dot {{ fill: var(--rh); }}
.g-open {{ fill: none; stroke: var(--ink); stroke-width: 1; }}
.g-mark {{ fill: var(--muted); font-size: 10px; text-anchor: middle; font-family: var(--body); }}
.shape {{ font-weight: 600; font-size: 16px; }}
.simp {{ display: block; color: var(--accent); font-style: italic; }}
.snd {{ display: block; color: var(--muted); font-size: 12.5px; }}
@media (max-width: 620px) {{
  .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .ch {{ font-size: 20px; }} .two .ch {{ font-size: 17px; }}
}}
@media print {{
  :root {{ --paper: #fff; --ink: #000; --muted: #555; --rule: #bbb; --accent: #444; --mark: #eee;
    --key: #fff; --keyline: #777; --keyblack: #222; --lh: #c48a1e; --rh: #7a5cc4; }}
  .sheet {{ padding-block: 0; }} .sec {{ margin-top: 14px; }} .bar {{ min-height: 60px; }}
}}
</style>
<main class="sheet">
  <div class="top">
    <div><p class="eyebrow">Lead sheet · Josie Faith</p><h1>Pancakes and Lemonade</h1></div>
    <dl class="meta">
      <div><dt>Key</dt><dd>E♭ major</dd></div>
      <div><dt>Tempo</dt><dd>♩ = 96</dd></div>
      <div><dt>Meter</dt><dd>4/4</dd></div>
      <div><dt>Length</dt><dd>{TOTAL} bars · 3:40</dd></div>
    </dl>
  </div>
  <ol class="form" aria-label="Form">{form_strip}</ol>
  <p class="howto">One box is one bar. Two chords in a box split the bar: the second chord lands on beat 3.
    Tap any chord to see <a href="#chords">how to play it</a> on piano and guitar.</p>
  {"".join(blocks)}
  {shapes_html}
  <div class="legend">
    <p><strong>Feel:</strong> mid-tempo, straight 16ths. The piano hook plays in bars 1–4 and comes back in the turnaround (33) and breakdown (63), where the vocal rests.</p><p><strong>Lyrics:</strong> placed from your chord sheet, roughly where each word lands. Where a box shows two chords, the second line of words starts around beat 3.</p>
    <p><strong>Notes in orange:</strong> what the band does: stops, fills, pull-backs. The tempo slows over bars 87–88.</p>
  </div>
</main>
'''
open(os.path.join(HERE, 'lead_sheet.html'), 'w').write(page)
print('wrote lead_sheet.html,', TOTAL, 'bars')
