# It's Rainin' Honey

A sister song to [Pancakes and Lemonade](../PANCAKESLEMONADE/): the same warmth, but
bright daytime instead of bittersweet morning. Piano-led, bouncy and a little cheeky. The
lyrics and vocal melody are still to be written.

A major (bridge borrows G with a Lydian ♯11), 104 BPM, 4/4 straight, 86 bars, 3:19.
Guitar: capo 2, no barre chords.

| File | What it is |
|---|---|
| `full_song_multitrack.mid` | **Open this in Logic.** Piano, drums, bass, Rhodes, shaker & tambourine |
| `piano_only.mid`, `drums_only.mid`, `bass_only.mid`, `rhodes_only.mid`, `aux_percussion_only.mid` | One instrument each, aligned to the multitrack |
| `chord_guide.mid` | Block chords for Logic's Chord Track |
| `lead_sheet.html` | Chart by bar with keyboard diagrams and blank lyric lines, plus piano and guitar shapes ([published copy](https://claude.ai/artifact/4RoNVWmLCoh5cwa1dE4ieu), private to josie) |
| `README_LOGIC.md` | **Start here:** sounds to load, section map, Chord Track, what was checked |
| `drum_map.md` | Every drum note (Logic names) and what the drums do per section |
| `song.py` | Chord chart, form and grooves, shared by every script |
| `generate_*.py`, `chord_shapes.py` | Rebuild everything |
| `validate_arrangement.py` | 64 checks, including originality against Pancakes |

To rebuild: `pip install mido`, then in this folder run
`python3 generate_piano.py && python3 generate_arrangement.py && python3 generate_chord_guide.py && python3 generate_lead_sheet.py`,
and check with `python3 validate_arrangement.py`.

Audio bounces and vocal recordings are not stored here because this repository is public.
