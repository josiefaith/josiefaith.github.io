"""Half Past Noon: the chord chart, form and grooves, shared by every generator.

A major, 4/4, 104 BPM, straight feel. Bridge borrows the flat-seven (G) with a Lydian #11.
Nothing here writes files; generate_piano.py, generate_arrangement.py, generate_chord_guide.py,
generate_lead_sheet.py and validate_arrangement.py all import it.
"""
import re

TITLE = 'Half Past Noon'
KEY = 'A'                # MIDI key signature
KEY_NAME = 'A major'
BPM = 104
PPQ = 480
S16 = PPQ // 4
BAR = S16 * 16
# ritardando over the last two bars: (bar, sixteenth, bpm)
RIT = [(-2, 0, 100), (-2, 8, 96), (-1, 0, 90), (-1, 8, 84)]

PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

# name: (bass pitch class, right-hand pitch classes, left-hand second-note interval)
# A=9 B=11 C#=1 D=2 D#=3 E=4 E#=5 F#=6 G=7 G#=8
CH = {
    'Aadd9':    (9,  [1, 4, 9, 11], 7),     # C# E A B
    'A6/9':     (9,  [1, 6, 11, 4], 7),     # C# F# B E
    'A/G':      (7,  [9, 1, 4], 12),        # A triad over G (the cheeky step down)
    'A/C#':     (1,  [4, 9, 1], 12),
    'D/F#':     (6,  [9, 2, 6], 12),
    'D6/9':     (2,  [6, 11, 4, 9], 7),     # F# B E A
    'Dmaj9':    (2,  [6, 9, 1, 4], 7),      # F# A C# E
    'Bm9':      (11, [2, 6, 9, 1], 7),      # D F# A C#
    'C#m7':     (1,  [4, 8, 11, 1], 7),     # E G# B C#
    'F#m9':     (6,  [9, 1, 4, 8], 7),      # A C# E G#
    'F#m7':     (6,  [9, 1, 4, 6], 7),
    'E9sus4':   (4,  [9, 11, 2, 6], 7),     # A B D F#
    'E':        (4,  [8, 11, 4], 7),
    'B9':       (11, [3, 9, 1, 6], 7),      # D# A C# F#   (V of V)
    'C#7':      (1,  [5, 11, 8, 1], 7),     # E# B G# C#   (V of vi)
    'Gmaj9':    (7,  [11, 2, 6, 9], 7),     # B D F# A     (borrowed flat-seven)
    'Gmaj7#11': (7,  [11, 1, 6, 2], 7),     # B C# F# D    (Lydian colour)
    'Em9':      (4,  [7, 11, 2, 6], 7),     # G B D F#     (borrowed minor five)
}

# semitones above the root, for the chord guide, the chord cards and the validator
QUALITY = {
    '': (0, 4, 7), 'add9': (0, 4, 7, 14), '6/9': (0, 4, 7, 9, 14), 'maj9': (0, 4, 7, 11, 14),
    'maj7#11': (0, 4, 7, 11, 18), 'm7': (0, 3, 7, 10), 'm9': (0, 3, 7, 10, 14),
    '7': (0, 4, 7, 10), '9': (0, 4, 7, 10, 14), '9sus4': (0, 5, 7, 10, 14),
}


def pc_of(s):
    return (PC[s[0]] + s[1:].count('#') - s[1:].count('b')) % 12


def parse(name):
    """'D/F#' -> (root pc, quality, bass pc, slash name or None)."""
    root, qual, slash = re.fullmatch(r'([A-G][#b]?)(6/9|[^/]*)(?:/([A-G][#b]?))?', name).groups()
    r = pc_of(root)
    return r, qual, (pc_of(slash) if slash else r), slash


def chord_tones(name):
    r, qual, bass, _ = parse(name)
    return {(r + i) % 12 for i in QUALITY[qual]} | {bass}


INTRO = [['Aadd9'], ['D6/9'], ['Aadd9'], ['E9sus4']]
VERSE = [['Aadd9'], ['A/G'], ['D/F#'], ['D6/9'],
         ['Bm9'], ['C#m7', 'F#m9'], ['Dmaj9'], ['E9sus4', 'E']]
PRE_1 = [['Bm9'], ['C#m7'], ['Dmaj9'], ['E9sus4', 'E']]
PRE_2 = [['Bm9'], ['C#m7', 'C#7'], ['F#m9', 'B9'], ['Dmaj9', 'E9sus4']]
CHORUS_A = [['A6/9'], ['C#m7'], ['Dmaj9'], ['B9'],
            ['A/C#'], ['Dmaj9'], ['Bm9', 'C#m7'], ['Dmaj9', 'E9sus4']]
CHORUS_B = [['A6/9'], ['C#7'], ['F#m9'], ['B9'],
            ['A/C#'], ['Dmaj9'], ['Bm9', 'C#m7'], ['Dmaj9', 'E9sus4']]
TURN = [['Aadd9'], ['F#m9', 'E9sus4']]
BRIDGE = [['Gmaj9'], ['Gmaj7#11'], ['Em9'], ['Em9', 'F#m7'],
          ['Gmaj9'], ['Gmaj7#11'], ['Bm9'], ['C#7']]
BREAKDOWN = [['F#m9'], ['Dmaj9', 'E9sus4']]
OUTRO = [['Aadd9'], ['D6/9'], ['Aadd9'], ['Dmaj9', 'E9sus4'], ['Aadd9'], ['Aadd9']]

# (section name, style, bars, piano velocity at first bar, at last bar)
FORM = [
    ('Intro',             'intro',        INTRO,          58, 62),
    ('Verse 1',           'verse',        VERSE,          50, 54),
    ('Verse 2',           'verse2',       VERSE,          53, 57),
    ('Pre-Chorus 1',      'pre',          PRE_1,          58, 68),
    ('Chorus 1',          'chorus_light', CHORUS_A,       66, 70),
    ('Turnaround',        'turn',         TURN,           62, 60),
    ('Verse 3',           'verse2',       VERSE,          56, 60),
    ('Pre-Chorus 2',      'pre',          PRE_2,          62, 78),
    ('Chorus 2',          'chorus',       CHORUS_B,       80, 84),
    ('Bridge',            'bridge',       BRIDGE,         52, 82),
    ('Breakdown',         'breakdown',    BREAKDOWN,      56, 60),
    ('Final Chorus',      'final',        CHORUS_B,       88, 94),
    ('Pull-back Chorus',  'pullback',     CHORUS_A[:4],   56, 60),
    ('Last Lift',         'final',        CHORUS_B[4:],   92, 98),
    ('Outro',             'outro',        OUTRO,          60, 44),
]


def sections():
    """[(name, style, start bar, end bar, chords)] with bar numbers filled in."""
    out, bar = [], 1
    for name, style, chords, *_ in FORM:
        out.append((name, style, bar, bar + len(chords) - 1, chords))
        bar += len(chords)
    return out


TOTAL_BARS = sum(len(f[2]) for f in FORM)
END = TOTAL_BARS * BAR


def timeline():
    """bar -> [(start16, len16, chord name)]"""
    tl, bar = {}, 1
    for _, _, chords, *_ in FORM:
        for bc in chords:
            half = 16 // len(bc)
            tl[bar] = [(k * half, half, c) for k, c in enumerate(bc)]
            bar += 1
    return tl


# ---------- rhythm identity (the originality check reads these) ----------
# hook: 16th positions of the piano hook's first bar
HOOK_RHYTHM = (0, 2, 3, 8, 10, 12)
# full chorus: right-hand chord hits, a 2+4+4+2+4 skip
CHORUS_CELL = (0, 2, 6, 10, 12)
# verse: right-hand chord hits on the backbeat (with the cross-stick)
VERSE_STABS = (4, 12)
# verse groove shared by kick, bass and piano left hand: 1, the "a" of 2, the "and" of 3
VERSE_KICK = (0, 7, 10)
