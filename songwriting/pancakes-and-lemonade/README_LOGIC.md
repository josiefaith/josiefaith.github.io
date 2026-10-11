# Pancakes and Lemonade: Logic Pro Guide

Version 2 of the arrangement, rebuilt around your lyrics. The first version is still in
`../original-piano-song/` and hasn't changed.

## What changed from version 1

- **A second verse** (bars 13–20), so your two opening verses both fit. The song is now 88 bars, **3:40.5**.
- **Chorus 1 is smaller.** The piano plays held chords with two soft pushes instead of the full
  bouncy pattern. The drums stay on brushes and the organ sits out. The big chorus sound now
  arrives at chorus 2 and grows into the final chorus.
- **Brushes.** A new **Drums (Brushes)** track plays from the intro through verse 3, again in the
  stripped-down chorus (bars 73–76), and in the outro. The regular kit (**Drums (Sticks)**)
  takes over at pre-chorus 2.
- **More room for your voice.** The piano no longer plays little melodies under your lines:
  - the end of each verse ("sweet syrup…", "look how the sun…")
  - the end of each chorus
  - the stripped-down chorus
  - the outro

  The piano hook stays where you aren't singing: the intro, the turnaround (bars 33–34) and the breakdown (bar 63).
- **The chords haven't changed.** Use the lead sheet's chords where they differ from your own sheet,
  for example Abm6 and Eb/G Gbdim7 in choruses 2 and 4.

## Song facts

| | |
|---|---|
| Key | E♭ major (bridge in G♭ major) |
| Tempo | 96 BPM, slowing over the last two bars (92 → 90 → 86 → 80) |
| Meter | 4/4 |
| Length | 88 bars, 3:40.5 |

## Files

| File | What it is |
|---|---|
| `full_song_multitrack.mid` | **Open this one.** Every instrument on its own track |
| `piano_only.mid`, `drums_only.mid`, `bass_only.mid`, `organ_only.mid`, `aux_percussion_only.mid` | One instrument each (drums_only has both drum tracks) |
| `chord_guide.mid` | Plain chords for filling Logic's Chord Track |
| `lead_sheet.html` | Chords by bar with your lyrics |
| `drum_map.md` | Every drum note and where brushes/sticks play |
| `generate_piano.py`, `generate_arrangement.py`, `generate_chord_guide.py`, `generate_lead_sheet.py` | Rebuild everything (`pip install mido`) |
| `validate_arrangement.py` | Re-checks the files (55 checks) |

## Tracks

| Track | MIDI ch. | Load in Logic (press **Y** for the Library) |
|---|---|---|
| Grand Piano | 1 | Piano → Steinway Grand Piano |
| **Drums (Brushes)** | 10 | a **brush kit**: type **brush** in the Library's search box |
| **Drums (Sticks)** | 10 | an acoustic kit (you used **Brooklyn**, which is a good choice) |
| Bass | 2 | your bass patch. Set the region's **Transpose to 0** if it shows +12 |
| Organ | 3 | Vintage B3 / Tonewheel Organ |
| Shaker & Tambourine | 10 | same kit as Drums (Sticks), optional |

**If your Logic has no brush kit:** load the same acoustic kit on the Brushes track. The part is
played very softly, so it still sounds like a gentle drummer, just with sticks instead of brushes.
In the Library, brush sounds may also sit inside a kit's own options. Names vary between Logic versions.

## Opening it

1. **File → Open…** → `full_song_multitrack.mid`. Say yes to tempo if asked.
2. Load a sound on each track (table above). Press Space to play.
3. Check the drums: solo **Drums (Brushes)**, open the Piano Roll, and click **C1** (kick),
   **D1** (snare / brush), **G#1** (hi-hat foot).
4. A track is silent? Use **Track → New Software Instrument Track**, drag the region onto it,
   load the sound, and delete the old track.

### Moving this into your current session
You already rebuilt the structure in your own session. To try my parts there instead of
starting over, drag the single-instrument files (for example `drums_only.mid` or `bass_only.mid`)
into new tracks at **bar 1**. They only line up if your session also has the 4-bar intro
and the new verse at bars 13–20.

## Chord Track
1. **File → Import → MIDI File…** → `chord_guide.mid` (no tempo import).
2. Show the Chord Track (**Track → Global Tracks → Show Chord Track**).
3. Option-drag the Chord Guide region onto it, then mute the Chord Guide track.

## Section map

| Bars | Section | Band |
|---|---|---|
| 1–4 | Intro | piano hook; brushes from bar 3 |
| 5–12 | Verse 1 | lightest brushes, bass roots |
| 13–20 | Verse 2 | 16th brush strokes, busier bass |
| 21–24 | Pre-Chorus 1 | builds, stops on beat 4 of bar 24 |
| 25–32 | Chorus 1 | held piano chords, brushed ride, no organ |
| 33–34 | Turnaround | piano hook |
| 35–42 | Verse 3 | busiest brushes, shaker, soft organ |
| 43–46 | Pre-Chorus 2 | **sticks in**, tom fill |
| 47–54 | Chorus 2 | first full-band chorus |
| 55–62 | Bridge (G♭) | half-time, then builds (vocalize "today") |
| 63–64 | Breakdown | drop out, hook; build on "look how the sun is shining" |
| 65–72 | Final Chorus | biggest |
| 73–76 | Final Chorus pull-back | brushes, half-time, very quiet |
| 77–80 | Lift | full band |
| 81–88 | Outro | brushes, fades; everyone ends on the downbeat of bar 88 |

## What was verified and what wasn't

**Verified by script** (all 55 checks pass):
- The files are valid Type 1 MIDI with 7 named tracks; every drum track is on channel 10.
- The tempo, meter and markers are the same on every track and file.
- No notes are stuck on, and every track ends exactly at the end of bar 88 (3:40.5).
- The bass plays the right bass note on all 107 chord changes, and the organ plays only chord tones.
- Brushes and sticks never play at the same time; they hand over mid-bar in bar 76.
- Chorus 1 measures quieter and thinner than chorus 2, which is thinner than the final chorus.

**Not tested** (needs Logic and ears):
- Which brush kit your Logic has.
- How chorus 1 actually feels now that it's lighter.
- Whether the lyric placement on the lead sheet matches how you actually sing it.
