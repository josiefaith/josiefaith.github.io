# Pancakes and Lemonade

Everything for the song, from the first piano sketch to the arrangement used in Logic.

| Folder | What's in it |
|---|---|
| `pancakes-and-lemonade/` | **Current version.** 88 bars, 3:40. Full band MIDI (`full_song_multitrack.mid` plus one file per instrument), chord guide, lead sheet with lyrics (`lead_sheet.html`), Logic guide (`README_LOGIC.md`), drum map, and the scripts that rebuild it all |
| `original-piano-song/` | The first piano-only version (80 bars, 3:20), `original_piano_song.mid` and its README |
| `original-piano-song/full-arrangement/` | Version 1 of the band arrangement around the original piano, with its own Logic guide and lead sheet |

Key E♭ major (bridge in G♭), 96 BPM, 4/4.

To rebuild the current version: `pip install mido`, then in `pancakes-and-lemonade/` run
`python3 generate_piano.py && python3 generate_arrangement.py && python3 generate_chord_guide.py && python3 generate_lead_sheet.py`,
and check with `python3 validate_arrangement.py`.

Audio bounces and vocal recordings are not stored here because this repository is public.
