#!/usr/bin/env python3
"""Build lead_sheet.html for It's Rainin' Honey: chords by bar with a keyboard diagram and an empty
lyric line under each, then one card per chord with the piano voicing and a barre-free guitar shape."""
import html
import os
import re

import chord_shapes as cs
from song import BPM, KEY_NAME, TITLE, TOTAL_BARS, sections

HERE = os.path.dirname(os.path.abspath(__file__))

# performance cues by bar (what the band does)
CUES = {
    1: 'piano hook', 3: 'drums enter', 13: 'ghost notes', 21: 'snare in', 25: 'light',
    33: 'piano hook', 35: 'shaker', 39: 'Rhodes', 46: 'tom fill', 47: 'full band',
    54: 'fill', 55: 'half-time', 59: 'climb', 63: 'drop out', 64: 'build', 65: 'biggest',
    72: 'stop on 3', 73: 'pull back', 76: 'build', 77: 'full band', 80: 'fill',
    82: 'Rhodes answers', 85: 'rit.', 86: 'hold',
}
NOTES = {
    'Chorus 1': 'Held chords, half the kit, no Rhodes: the big chorus waits',
    'Chorus 2': 'First full-band chorus',
    'Bridge': 'Borrowed G (♭VII) with a Lydian ♯11',
    'Breakdown': 'Piano hook; you rest in bar 63',
    'Pull-back Chorus': 'As quiet as verse 1',
    'Last Lift': 'Loudest four bars',
}


def acc(s):
    return s.replace('b', '♭').replace('#', '♯')


def slug(name):
    return 'c-' + re.sub(r'[^A-Za-z0-9]+', '-', name.replace('#', 's').replace('/', '-over-')).strip('-')


def chord_html(name, link=True):
    m = re.fullmatch(r'([A-G][#b]?)(m(?!aj))?(6/9|[^/]*)(?:/([A-G][#b]?))?', name)
    root, minor, ext, bass = m.groups()
    out = f'<span class="rt">{acc(root)}{"m" if minor else ""}</span>'
    if ext:
        out += f'<sup>{acc(ext)}</sup>'
    if bass:
        out += f'<span class="sl">/{acc(bass)}</span>'
    if link:
        return f'<a class="ch" href="#{slug(name)}">{out}</a>'
    return f'<span class="ch">{out}</span>'


SECS = sections()
form_strip = ''.join(
    f'<li><span class="fs-name">{html.escape(n)}</span>'
    f'<span class="fs-bars">{a}–{b}</span></li>' for n, _, a, b, _ in SECS)

VOICINGS = cs.piano_voicings()
blocks = []
for name, _, start, end, chords in SECS:
    cells = []
    for i, bc in enumerate(chords):
        bno = start + i
        cue = CUES.get(bno, '')
        cols = ''.join(f'<div class="col">{chord_html(c)}{cs.piano_svg(*VOICINGS[c], c)}'
                       f'<span class="ly" aria-label="lyric line, bar {bno}"></span></div>' for c in bc)
        cells.append(
            f'<div class="bar{" two" if len(bc) == 2 else ""}{" end" if bno == TOTAL_BARS else ""}">'
            f'<span class="bn">{bno}</span><div class="chords">{cols}</div>'
            f'{f"<span class=cue>{cue}</span>" if cue else ""}</div>')
    note = NOTES.get(name, '')
    blocks.append(
        f'<section class="sec"><header><h2>{html.escape(name)}</h2>'
        f'<span class="range">bars {start}–{end}</span>'
        f'{f"<span class=note>{note}</span>" if note else ""}</header>'
        f'<div class="grid">{"".join(cells)}</div></section>')

# ---------- chord cards ----------
CAPO, SHAPES, _ = cs.guitar_shapes(list(VOICINGS))
cards = []
for name, (lh, rh) in VOICINGS.items():
    (score, combo), easy = SHAPES[name]
    missing = cs.missing_colour(name, combo, CAPO)
    lh_txt = ' '.join(cs.with_octave(p, name) for p in lh)
    rh_txt = ' '.join(cs.with_octave(p, name) for p in rh)
    simp = (f'<span class="simp">Easier version: leaves out {" and ".join(missing)}</span>'
            if easy and missing else '')
    cards.append(
        f'<article class="card" id="{slug(name)}"><h3>{chord_html(name, link=False)}</h3>'
        f'<div class="pn">{cs.piano_svg(lh, rh, name)}'
        f'<p class="vn"><span class="tag t-lh">LH</span> {lh_txt}'
        f' <span class="tag t-rh">RH</span> {rh_txt}</p></div>'
        f'<div class="gt">{cs.guitar_svg(combo, name)}'
        f'<p><span class="shape">{cs.shape_name(name, CAPO, combo, easy)}</span> shape · capo {CAPO}<br>{simp}'
        f'<span class="snd">Sounds: {cs.sounding_notes(combo, CAPO, name)}</span></p></div></article>')
shapes_html = f'''<section class="shapes" id="chords">
    <h2 class="sh">How to play the chords</h2>
    <p class="howto">Every chord in the song, in the order it first appears. Tap a chord in the chart above to jump here.</p>
    <p class="howto"><strong>Piano:</strong> the voicing the piano in the track plays most often.
      <span class="tag t-lh">LH</span> left hand (bass note plus a 5th or octave), <span class="tag t-rh">RH</span> right hand,
      kept around G3–G4 so it sits under your voice. The dot under the keyboard marks middle C (C4). Numbers on the
      keys are suggested fingers: 1 = thumb, 5 = pinky, in both hands.</p>
    <p class="howto"><strong>Guitar:</strong> <strong>capo on fret {CAPO}</strong>, open shapes only, no barre chords, all
      within four frets of the capo. The shape name is what your fingers make with the capo on. × means don't play
      that string; ○ means play it open. Numbers in the dots are fretting fingers: 1 = index, 2 = middle,
      3 = ring, 4 = pinky. Shapes marked "easier version" leave out one colour note, which the piano still plays.</p>
    <div class="cards">{"".join(cards)}</div>
  </section>'''

minutes = '3:19'
page = f'''<title>{TITLE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Lora:ital,wght@0,400;0,600;1,400&family=Reenie+Beanie&display=swap">
<style>
/* Layout: a printed chart, the Pancakes lead sheet in daylight. Four bars to a line, barlines between bars,
   section names as rehearsal marks, a blank lyric line under every chord. */
:root {{
  --paper: #fdfaf1; --ink: #2a2140; --muted: #6c6280; --rule: #d6cddf;
  --accent: #9a5d00; --mark: #fff0c9;
  --key: #ffffff; --keyline: #8d84a0; --keyblack: #2a2140; --lh: #e0a12a; --rh: #7a5cc4;
  --fn-lh: #2a2140; --fn-rh: #ffffff; --line: #c9bfd6;
  --display: "Playfair Display", Georgia, serif;
  --body: "Lora", Georgia, serif;
  --hand: "Reenie Beanie", "Bradley Hand", cursive;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #1b1529; --ink: #efe8f8; --muted: #a99dbd; --rule: #3e3456;
  --accent: #f0bd5e; --mark: #3a2f1a; color-scheme: dark;
  --key: #e9e4f1; --keyline: #3e3456; --keyblack: #120d1d; --lh: #f0bd5e; --rh: #a78bea;
  --fn-lh: #1b1529; --fn-rh: #1b1529; --line: #4a3f63; }} }}
:root[data-theme="dark"] {{
  --paper: #1b1529; --ink: #efe8f8; --muted: #a99dbd; --rule: #3e3456;
  --accent: #f0bd5e; --mark: #3a2f1a; color-scheme: dark;
  --key: #e9e4f1; --keyline: #3e3456; --keyblack: #120d1d; --lh: #f0bd5e; --rh: #a78bea;
  --fn-lh: #1b1529; --fn-rh: #1b1529; --line: #4a3f63; }}
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
.howto a {{ color: var(--accent); }}
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
.chords {{ display: flex; flex-wrap: wrap; width: 100%; gap: 10px 12px; min-width: 0; }}
.col {{ flex: 1 1 150px; min-width: 0; display: flex; flex-direction: column; gap: 4px; }}
.ly {{ display: block; height: 22px; border-bottom: 1px dashed var(--line); }}
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
a.ch:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }}
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
.t-lh {{ background: var(--lh); color: var(--fn-lh); }} .t-rh {{ background: var(--rh); }}
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
  .sheet {{ padding-inline: 16px; }}
  .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .ch {{ font-size: 20px; }} .two .ch {{ font-size: 17px; }}
}}
@media print {{
  :root {{ --paper: #fff; --ink: #000; --muted: #555; --rule: #bbb; --accent: #444; --mark: #eee;
    --key: #fff; --keyline: #777; --keyblack: #222; --lh: #c48a1e; --rh: #7a5cc4; --line: #999; }}
  .sheet {{ padding-block: 0; }} .sec {{ margin-top: 14px; }} .bar {{ min-height: 60px; }}
}}
</style>
<main class="sheet">
  <div class="top">
    <div><p class="eyebrow">Lead sheet · Josie Faith · sister song to Pancakes and Lemonade</p><h1>{TITLE}</h1></div>
    <dl class="meta">
      <div><dt>Key</dt><dd>{KEY_NAME}</dd></div>
      <div><dt>Tempo</dt><dd>♩ = {BPM}</dd></div>
      <div><dt>Meter</dt><dd>4/4, straight</dd></div>
      <div><dt>Length</dt><dd>{TOTAL_BARS} bars · {minutes}</dd></div>
      <div><dt>Guitar</dt><dd>capo {CAPO}</dd></div>
    </dl>
  </div>
  <ol class="form" aria-label="Form">{form_strip}</ol>
  <p class="howto">One box is one bar. Two chords in a box split the bar: the second chord lands on beat 3.
    The dashed line under each chord is for your lyrics. Tap any chord to see <a href="#chords">how to play it</a> on piano and guitar.</p>
  {"".join(blocks)}
  {shapes_html}
  <div class="legend">
    <p><strong>Feel:</strong> bright and bouncy, straight 16ths. The kick, bass and piano left hand share a syncopated
      rhythm in the verses (1, the "a" of 2, the "and" of 3) while the piano answers on 2 and 4.</p>
    <p><strong>Room for your voice:</strong> the piano plays its hook only in the intro (1–4), turnaround (33–34),
      breakdown (63) and outro tag (81–85). Everywhere else it only comps.</p>
    <p><strong>Handwritten notes:</strong> what the band does: entrances, fills, stops. The tempo slows over bars 85–86.</p>
  </div>
</main>
'''
open(os.path.join(HERE, 'lead_sheet.html'), 'w').write(page)
print('wrote lead_sheet.html,', TOTAL_BARS, 'bars, capo', CAPO)
