# Full Arrangement: Logic Pro Guide

The original piano song with a band added around it: drums, bass, organ and a
shaker/tambourine track. The piano part is the original, unchanged note for note.

## The song at a glance

| | |
|---|---|
| **Key** | E♭ major (the bridge moves to G♭ major) |
| **Tempo** | 96 BPM. It slows down over the last 2 bars: 92 → 90 → 86 → 80 |
| **Meter** | 4/4 |
| **Length** | 80 bars, **3:20.5** |
| **Feel** | Straight 16th notes, mid-tempo |
| **Singer** | Alto. Verses leave the middle register mostly clear; the band thins out under every vocal-length phrase. |

## Files in this folder

| File | What it is |
|---|---|
| `full_song_multitrack.mid` | **Start here.** All instruments, each on its own named track |
| `piano_only.mid` | The original piano MIDI (identical copy) |
| `drums_only.mid` | Drums only |
| `bass_only.mid` | Bass only |
| `organ_only.mid` | Organ only |
| `aux_percussion_only.mid` | Shaker & tambourine only |
| `chord_guide.mid` | Plain block chords for filling Logic's Chord Track (see below). Not meant to be heard |
| `drum_map.md` | Which note number is which drum, and how loud things are |
| `generate_chord_guide.py` | Rebuilds `chord_guide.mid` |
| `generate_arrangement.py` | Rebuilds everything (`pip install mido`, then `python3 generate_arrangement.py`) |
| `validate_arrangement.py` | Re-checks all the files |

Every file has the same tempo map and markers and starts at bar 1. You can drag
any single-instrument file into a project and it will line up.

## Tracks and MIDI channels

| # | Track name | MIDI ch. | GM sound requested | Load this in Logic |
|---|---|---|---|---|
| 1 | Tempo & Meter | — | (tempo, 4/4, key, markers) | nothing to load |
| 2 | Grand Piano | 1 | 1 Acoustic Grand Piano | Piano → **Steinway Grand Piano** |
| 3 | Drums | **10** | GM drum kit | Drums → an **acoustic** kit (see below) |
| 4 | Bass | 2 | 34 Electric Bass (finger) | Bass → a **fingerstyle / studio electric bass** |
| 5 | Organ | 3 | 17 Drawbar Organ | Keyboards/Organ → **Vintage B3** (any warm B3 patch) |
| 6 | Shaker & Tambourine | **10** | GM percussion | same acoustic kit as the drums (optional track) |

> **Important:** the GM sound numbers above are just labels. **Logic does not
> pick its own sounds from them**, so you choose each sound yourself (step 3
> below). This takes about two minutes.

## Step by step: open it and hear it

### 1. Open the file
1. In Logic: **File → Open…** and choose `full_song_multitrack.mid`.
   - This creates a new project with the tempo, the slowdown at the end, 4/4,
     the key and the section markers (Intro, Verse 1…) already in place.
2. If Logic asks about **tempo**, choose to import it.

> If you'd rather add it to a project you already have: **File → Import → MIDI File…**.
> Say yes to importing tempo, or the song will play at the wrong speed and the ending won't slow down.

### 2. Check that you have 5 instrument tracks
You should see **Grand Piano, Drums, Bass, Organ, Shaker & Tambourine**, each
with one long green region from bar 1 to bar 80.

### 3. Give every track a sound
Do this for each track:
1. Click the track's name.
2. Press **Y** to open the **Library**.
3. Click a sound (see the table above). Press **Space** to play and listen.

**Drums: what to choose**
- In the Library open **Drums** (or **Drum Kit**) and pick an **acoustic** kit.
  Good choices are the Drum Kit Designer kits, such as *SoCal*, *Brooklyn* or
  *Portland*. Names vary a little between Logic versions.
- **Avoid** anything called *Drum Machine*, *Electronic*, *Beat* or a genre
  like *Trap*. Those are electronic sounds with a different note layout.
- **Don't use a Drummer track.** Drummer makes up its own part. This MIDI
  is the drum part.

**Shaker & Tambourine:** load the **same acoustic kit** on this track. Some kits
include a tambourine and shaker and some don't. If you hear nothing from this
track, either try another kit or just mute it, because it's optional. You can
also move its regions onto the Drums track.

### 4. Check the drums are mapped right (30 seconds)
1. **Solo** the Drums track (the **S** button) and press Space. You should hear a
   steady, gentle groove from bar 3.
2. Double-click the Drums region to open the **Piano Roll**. Click the
   keyboard on the left:
   - **C1** (MIDI note 36): you should hear the **kick**
   - **D1** (38): you should hear the **snare**
   - **F#1** (42): you should hear a **closed hi-hat**
   - C#1 (37) is cross-stick, D#2 (51) is ride, C#2 (49) is crash
3. If C1 isn't a kick, the loaded kit isn't a standard acoustic kit. Pick
   a different one from the Library.

Logic calls middle C **C3**, which is why note 36 shows up as **C1**.
The full list is in `drum_map.md`.

### 5. If a track makes no sound (fallback)
Sometimes a track imports as an *External MIDI* track, which sends notes out of the
computer instead of playing a sound. Fix:
1. **Track → New Software Instrument Track.** It usually opens with a piano.
2. **Drag the green region** from the silent track onto the new track. Hold
   nothing while dragging, and drop it at bar 1.
3. Load the right sound on the new track (step 3) and delete the old one.

Also check that the track's **M** (mute) isn't lit, the fader isn't at the bottom, and
**Logic Pro → Settings → Audio → Output Device** is your speakers/headphones.

### 6. Changing a sound later
Click the track and pick a different patch in the Library (**Y**). The notes stay the same.
Some ideas: swap the bass for an upright bass, or the organ for a soft string pad.

## Sections, bars and chords

Two chords written in one bar change on beat 3.

| Bars | Section | Chords |
|---|---|---|
| 1–4 | Intro | Ebmaj9 · Bb/D · Abmaj7/C · Bb9sus4 |
| 5–12 | Verse 1 | Ebmaj9 · Bb/D · Cm9 · Cm7/Bb · Abmaj9 · Gm11 C7b9 · Fm9 · Bb9sus4 Bb9 |
| 13–16 | Pre-Chorus 1 | Abmaj9 · Am7b5 D7b9 · Gm11 Gb9 · Fm7 Bb9sus4 |
| 17–24 | Chorus 1 | Abmaj9 · Bb/Ab · Gm11 · C7b9 · Fm9 · Bb13 · Gm11 Cm7 · Fm7 Bb9sus4 |
| 25–26 | Turnaround | Ebmaj9 · Ab/Bb |
| 27–34 | Verse 2 | same as Verse 1 |
| 35–38 | Pre-Chorus 2 | Abmaj9 · Am7b5 D7b9 · Gm11 Gb9 · Fm9 Bb13 |
| 39–46 | Chorus 2 | Abmaj9 · Bb/Ab · Gm11 · C7b9 · Fm9 · Abm6 · Eb/G Gbdim7 · Fm7 Bb9sus4 |
| 47–54 | Bridge (G♭) | Cbmaj9 · Db/Cb · Bbm9 · Ebm9 · Abm9 · Db13 · Gbmaj9 · Gbmaj7#11 |
| 55–56 | Breakdown | Abm6 · Bb9sus4 Bb7b9 |
| 57–64 | Final Chorus | same as Chorus 1 |
| 65–72 | Final Chorus (pull-back + lift) | same as Chorus 2 |
| 73–80 | Outro | Ebmaj9 · Bb/D · Abmaj7/C · Abm6/Cb · Ebmaj9/Bb · Ab/Bb · Ebmaj9 · Ebmaj9 |

## Getting the chord symbols into Logic (Chord Track)

MIDI files can't carry Logic chord symbols. `chord_guide.mid` lets Logic work them out.
It holds every chord spelled plainly, with the bass note underneath. You need Logic Pro 11 or later; menu names may vary slightly.

1. **File → Import → MIDI File…** → `chord_guide.mid`. Skip importing tempo, because it's identical anyway.
   You get a track called **Chord Guide (mute me)**. Make sure its region starts at bar 1.
2. Show the Chord Track: **Track → Global Tracks → Show Chord Track** (or press **G**).
3. **Option-drag** the Chord Guide region up onto the Chord Track (Option makes a copy). Logic analyzes it
   and fills in the chords.
4. **Mute** the Chord Guide track (**M**) or delete it.
5. Spot-check a few bars against the table above. Logic may simplify extended chords (e.g. Gm11 → Gm7)
   or write some chords differently. Double-click any chord on the Chord Track to fix it.

## Who plays what, section by section

| Bars | Section | Drums | Bass | Organ | Shaker/Tamb. |
|---|---|---|---|---|---|
| 1–4 | Intro | none for 2 bars, then soft hats + snare pickup | enters bar 3, long notes | — | — |
| 5–12 | Verse 1 | kick + cross-stick + 8th hats (restrained) | roots locked to the kick | — | — |
| 13–16 | Pre 1 | real snare, building; band stops on beat 4 of bar 16 | 8th-note pulse | — | — |
| 17–24 | Chorus 1 | crash, fuller kick, hats, ghost notes | chorus groove with pickups | soft held chords | — |
| 25–26 | Turnaround | light | held notes | — | — |
| 27–34 | Verse 2 | 16th hats, ghost snares, kick pickups | busier line | soft pad from bar 31 | shaker from bar 29 |
| 35–38 | Pre 2 | building, tom fill into chorus | 8th pulse | swell | shaker |
| 39–46 | Chorus 2 | ride cymbal, fuller | + octave pops | held chords | shaker |
| 47–50 | Bridge | **half-time**: snare on beat 3, ride | whole notes | slow swells | — |
| 51–54 | Bridge climb | builds to a snare roll | quarters → 8ths | rising swell | — |
| 55–56 | Breakdown | one crash, silence, snare crescendo | held, then 8ths | swell into final chorus | — |
| 57–64 | Final Chorus | strongest groove, ride bell, crashes | full | held chords | tambourine on 2 & 4 |
| 65–68 | Pull-back | kick, cross-stick, hat foot only, then tom fill | whole notes | soft, then swell | — |
| 69–72 | Lift | full band | full | chords + small off-beat lifts | tambourine |
| 73–80 | Outro | fades to ride only; final kick + crash together | long notes | soft fade-out | — |

Everyone plays the last chord together on the downbeat of bar 80, and the file ends at the end of that bar.

## Mixing starting points
- The organ is intentionally quiet (MIDI volume 84). It's meant to be felt, not heard.
  Turn it down or mute it if it fights the vocal.
- Faders: piano loudest, bass and drums just under it, organ and shaker well below.
- To record your vocal: **Track → New Audio Track**, arm it (**R**), and sing along.

## What was verified and what wasn't

**Verified by script** (`validate_arrangement.py`, 47 checks, all pass):
- The files are valid Type 1 MIDI with 6 named tracks at 480 PPQ.
- The tempo map, 4/4, key and markers are identical to the original's.
- The piano track is identical to the original, and `piano_only.mid` is byte-identical.
- The drums are on channel 10 and use only documented GM notes. Bass is on ch. 2, organ on ch. 3.
- No notes are stuck on and no notes fall outside bars 1–80. Everything ends exactly at the end of bar 80 (3:20.5).
- The bass plays the right bass note on all 97 chord changes, and the organ plays only chord tones.
- 209 of 216 kicks land together with a bass note.
- Each single-instrument file matches its track in the multitrack file exactly.

**Not yet tested** (needs Logic and ears):
- How Logic names and sets up the tracks on import, for example whether any
  import as External MIDI. The fallback in step 5 covers that.
- Whether your chosen kit includes a shaker (note 82) and tambourine (note 54).
- Whether Vintage B3 responds to the organ swells. The swells use CC11
  (expression). If they don't come through, the organ still plays; it just won't swell.
- How it actually sounds. Nobody has listened to it yet; it was checked by analysis only.
