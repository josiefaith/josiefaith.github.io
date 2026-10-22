# Half Past Noon: Logic Pro Guide

A sister song to *Pancakes and Lemonade*. Pancakes is the bittersweet morning; this one is
bright daytime: sunnier, bouncier, a little cheeky. The piano leads, and the band leaves room
for your lyrics and melody.

## Song facts

| | |
|---|---|
| Key | A major (the bridge borrows G major, the flat-seven, with a Lydian ♯11) |
| Tempo | 104 BPM, slowing over the last two bars (100 → 96 → 90 → 84) |
| Meter | 4/4, straight 16ths (no swing) |
| Length | 86 bars, **3:19** |
| Vocal zone | written for an alto melody around F3–D5; the tonic A sits at A3 and A4 |
| Guitar | **capo 2**, open G-family shapes, no barre chords |

## Files

| File | What it is |
|---|---|
| `full_song_multitrack.mid` | **Open this one.** Every instrument on its own track |
| `piano_only.mid`, `drums_only.mid`, `bass_only.mid`, `rhodes_only.mid`, `aux_percussion_only.mid` | One instrument each, same tempo map, lined up with the multitrack |
| `chord_guide.mid` | Plain block chords for filling Logic's Chord Track |
| `lead_sheet.html` | Chords by bar with a keyboard under each and a blank line for lyrics, then piano and guitar shapes for every chord |
| `drum_map.md` | Every drum note and what the drums do in each section |
| `song.py` | The chord chart and form (every script reads it) |
| `generate_piano.py`, `generate_arrangement.py`, `generate_chord_guide.py`, `generate_lead_sheet.py`, `chord_shapes.py` | Rebuild everything |
| `validate_arrangement.py` | Re-checks every file (64 checks) |

## Tracks

| Track | MIDI ch. | Load in Logic (press **Y** for the Library) |
|---|---|---|
| Grand Piano | 1 | Piano → **Steinway Grand Piano** |
| Drums | 10 | Drum Kit → an acoustic kit: **Brooklyn** or **SoCal** |
| Bass | 2 | Bass → a fingerstyle electric bass (**Fingerstyle Bass** or **Liverpool Bass**). Set the region's **Transpose to 0** if it shows +12 |
| Rhodes | 3 | Electric Piano → **Vintage Electric Piano** (Suitcase or Mark I) |
| Shaker & Tambourine | 10 | the same kit as Drums (or Percussion → a shaker/tambourine kit) |

The program changes in the file are only labels. Logic won't pick these sounds by itself, so load
each one from the Library.

## Opening it

1. **File → Open…** → `full_song_multitrack.mid`. Say yes if Logic asks about the tempo.
2. Click each track, press **Y**, and load the sound from the table above.
3. Press **Space** to play.
4. Check the drums: solo **Drums**, double-click the region to open the Piano Roll, and look for
   **C1** (kick), **D1** (snare), **C♯1** (cross-stick) and **F♯1** (closed hi-hat). If those
   hit the wrong drums, the kit isn't a General MIDI kit. Pick an acoustic kit from the Drum Kit folder.
5. **A track makes no sound?** Use **Track → New Software Instrument Track**, load the sound, drag
   the region onto the new track at bar 1, and delete the old track.

### Volume faders
The files contain **no volume (CC7) or pan (CC10) messages**, so every fader and pan knob is yours.
The piano uses the sustain pedal (CC64) and the Rhodes uses expression (CC11) for its swells; neither
moves a fader.

Starting levels: Piano 0 dB, Bass −3 dB, Drums −4 dB, Rhodes −10 dB (pan a little right),
Shaker & Tambourine −14 dB (pan a little left). Then set them by ear around your vocal.

## Chord Track
1. **File → Import → MIDI File…** → `chord_guide.mid` (don't import its tempo).
2. Show the Chord Track: **Track → Global Tracks → Show Chord Track**.
3. Option-drag the Chord Guide region up onto the Chord Track; Logic reads the chords from it.
4. Mute the "Chord Guide (mute me)" track.

## Section map

| Bars | Section | Chords (two in a bar = second on beat 3) | Band |
|---|---|---|---|
| 1–4 | Intro | A(add9) · D6/9 · A(add9) · E9sus4 | piano hook; soft hats from bar 3 |
| 5–12 | Verse 1 | A(add9) · A/G · D/F♯ · D6/9 · Bm9 · C♯m7 F♯m9 · Dmaj9 · E9sus4 E | kick on 1, the "a" of 2 and the "and" of 3; cross-stick and piano on 2 and 4 |
| 13–20 | Verse 2 | same as verse 1 | adds ghost snares and a 16th skip in the hats |
| 21–24 | Pre-Chorus 1 | Bm9 · C♯m7 · Dmaj9 · E9sus4 E | real snare; climbs one step per bar |
| 25–32 | Chorus 1 | A6/9 · C♯m7 · Dmaj9 · B9 · A/C♯ · Dmaj9 · Bm9 C♯m7 · Dmaj9 E9sus4 | small: held piano chords, half the kit, no Rhodes |
| 33–34 | Turnaround | A(add9) · F♯m9 E9sus4 | piano hook |
| 35–42 | Verse 3 | same as verse 1 | shaker joins; Rhodes pads from bar 39 |
| 43–46 | Pre-Chorus 2 | Bm9 · C♯m7 C♯7 · F♯m9 B9 · Dmaj9 E9sus4 | Rhodes swells, tom fill |
| 47–54 | Chorus 2 | A6/9 · **C♯7** · **F♯m9** · B9 · A/C♯ · Dmaj9 · Bm9 C♯m7 · Dmaj9 E9sus4 | first full-band chorus |
| 55–62 | Bridge | Gmaj9 · Gmaj7♯11 · Em9 · Em9 F♯m7 · Gmaj9 · Gmaj7♯11 · Bm9 · C♯7 | half-time, Rhodes swells; climbs back from bar 59 |
| 63–64 | Breakdown | F♯m9 · Dmaj9 E9sus4 | piano hook alone (you rest), then a build |
| 65–72 | Final Chorus | as chorus 2 | biggest: ride bell, tambourine; stops on beat 3 of bar 72 |
| 73–76 | Pull-back Chorus | A6/9 · C♯m7 · Dmaj9 · B9 | as quiet as verse 1 |
| 77–80 | Last Lift | A/C♯ · Dmaj9 · Bm9 C♯m7 · Dmaj9 E9sus4 | full band, loudest bars |
| 81–86 | Outro | A(add9) · D6/9 · A(add9) · Dmaj9 E9sus4 · A(add9) · A(add9) | hook tag with Rhodes answers; rit.; everyone on the last downbeat |

**The harmony in one line:** home is A with added 9ths and 6ths; the secondary dominants are
B9 (V of V) and C♯7 (V of vi); the bridge borrows G major from A Mixolydian and colours it Lydian
with C♯ (the ♯11). There are no minor-seven-flat-five or flat-nine chords.

## What was verified and what wasn't

**Verified by `validate_arrangement.py`** (64 checks, all passing):
- Valid Type 1 MIDI at 480 PPQ with 6 named tracks. Drums and percussion are on channel 10; no CC7 or CC10 anywhere.
- Tempo, meter (4/4), key (A) and 15 section markers are identical in every file, and the markers
  sit on the section boundaries.
- 3:19 long. No stuck notes, nothing outside bars 1–86, and every track ends exactly on the last
  barline. All five instruments play the last downbeat together.
- Drum notes all come from the General MIDI map and match `drum_map.md`. The bass stays inside E1–G3.
- The bass plays the chord's bass note on all 106 chord changes from bar 3. The Rhodes and the
  chord guide play only chord tones. 99% of kicks land with a bass note.
- Loudness: verse 1 is 7.1 dB quieter than the final chorus. The pull-back chorus is within
  1.7 dB of verse 1. Chorus 1 < chorus 2 < final chorus.
- Every guitar shape is barre-free within four frets of capo 2. Piano hands span at most a ninth,
  and 93% of right-hand chord notes sit between G3 and G4.
- Originality vs Pancakes: different key, no four-chord sequence in common (compared as scale
  degrees, so a transposed copy would also be caught), a different hook rhythm, and a different
  chorus rhythm cell.

**Not verified** (needs Logic and your ears):
- How it actually sounds with real patches, and the balance with your voice.
- Whether chorus 1 feels big enough. It is deliberately smaller than chorus 2 and measures a little
  under the end of pre-chorus 1. If the lift into it feels like a drop, nudge the chorus 1 drums up a few dB.
- Whether the A major key and the melody zone suit the melody you write. If they don't, transpose
  every region by the same amount. The guitar capo then moves with it.

## Rebuild

```bash
pip install mido
python3 generate_piano.py && python3 generate_arrangement.py && python3 generate_chord_guide.py && python3 generate_lead_sheet.py
python3 validate_arrangement.py
```
Each instrument has its own fixed random seed, so the files rebuild identically, and changing one
part never shifts another.
