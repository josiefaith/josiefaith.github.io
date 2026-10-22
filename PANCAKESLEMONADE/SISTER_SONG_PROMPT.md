Working title: ____________ (leave blank and you choose one; tell me what you picked)

# Task: compose and produce a sister song to "Pancakes and Lemonade"

You are an expert songwriter, pianist, arranger, drummer, bassist, MIDI programmer and Logic Pro
production assistant. Create a brand-new, original piano-led song for me, Josie Faith (alto
singer-songwriter). I will write the lyrics and vocal melody myself on top of the MIDI tracks you make.
Execute everything: generate the real files, validate them, commit and push. Don't stop at a plan.

## Read this first
This repo already contains the first song, in `PANCAKESLEMONADE/`. Read
`PANCAKESLEMONADE/pancakes-and-lemonade/` (the generators, `chord_shapes.py`,
`validate_arrangement.py`, `README_LOGIC.md`, `lead_sheet.html`) to learn the file formats, code
patterns and deliverables. **Reuse and adapt the code freely, but not the music.** Its key, chords,
motifs, rhythms and structure must not be copied.

Put everything for the new song in a new top-level folder named after the working title in capitals
with no spaces (like `PANCAKESLEMONADE`). Don't modify anything in `PANCAKESLEMONADE/`.

## Creative direction
- Inspiration: the broad sensibilities of Jackie Evans ("Leave You", "Sleep For Days"): piano-led
  pop with jazzy harmony, conversational phrasing, rhythmic momentum and emotional storytelling. Also
  the warmth of Pancakes and Lemonade. Copy nothing identifiable from either.
- Mood: **sunnier and more playful than Pancakes**: cheeky, upbeat, everyday joy. Pancakes is
  bittersweet morning; this one is bright daytime.
- Feel: **brighter and bouncier**, about **100–110 BPM**, straight feel, 4/4. Give it its own rhythmic
  identity. Don't reuse Pancakes' 3+3+2 chorus pattern, its 5-note hook rhythm or its verse stab
  positions.
- Harmony: colorful but **happy**: major-key home, add9 / 6/9 / maj7 / sus / slash chords, a secondary
  dominant or two, a Lydian or borrowed color for the bridge. Fewer dark altered chords than Pancakes
  (it used 7♭9 and m7♭5). Purposeful voice leading.
- **Key: not E♭ major, and don't use G♭ for the bridge.** Pick a key that suits an alto voice (melody
  zone roughly F3–D5) and lets guitar use easy open shapes with a capo (see Playability).
- Length: **3:00–4:00**. Calculate bars and duration mathematically before composing.
- Structure: intro, verse 1, verse 2 (or another way to fit two verses before the first pre-chorus),
  pre-chorus, chorus 1, turnaround, verse 3, pre-chorus 2, chorus 2, a bridge that is a real departure,
  breakdown, final chorus, a quiet pulled-back chorus, a last lift, outro. Adjust if the song wants it.

## Arrangement rules (lessons from the first song; follow these)
1. **Leave room for the vocal.** The piano plays no melodic fills or countermelodies under sung lines.
   A piano hook is welcome only where the vocal rests: intro, turnaround, breakdown, outro tag.
2. **Build in layers.** Chorus 1 is clearly smaller than chorus 2 (lighter piano pattern, softer drums,
   no Rhodes). Chorus 2 is the first full-band chorus. The final chorus is biggest, followed by a quiet
   pulled-back chorus and then the last lift.
3. **Design the arc in the arrangement, not only with velocity.** My vocal will sit at a steady level,
   so verses must be genuinely sparser and quieter than choruses. Validate this: measured the same way
   as `validate_arrangement.py`, the full band should be at least 3 dB quieter in verse 1 than in the
   final chorus. The pulled-back chorus should be about as quiet as verse 1.
4. **Drums: acoustic kit, General MIDI notes on channel 10, no brushes track.** I liked the Pancakes
   version-1 drums: kick locked to the bass and piano, cross-stick in verses, hats, real snare from the
   pre-chorus, crash into choruses, ghost notes, tom fills that land cleanly. Write in that spirit but
   with a bouncier groove of its own, a half-time or otherwise contrasting bridge, and a natural ending.
   Light tambourine or shaker on its own track only where it helps.
5. **Bass:** fingerstyle electric bass, range E1–G3 (MIDI 28–55). Lock with the kick, use passing notes
   on phrase ends, and keep fills restrained.
6. **Rhodes instead of organ:** an electric piano (GM program 5, Electric Piano 1). Sparse comping,
   soft pads and small answers. Never in chorus 1. Stay out of the vocal's way.
7. **Piano is the center.** Two-handed, playable, consistent left-hand patterns with tasteful variation.

## Playability
- **Guitar: no barre chords.** Use a capo (allowed) and open shapes within the first four frets above
  it. Use the search approach from `PANCAKESLEMONADE/pancakes-and-lemonade/chord_shapes.py`, but
  forbid barres. Choose the key and capo together so that **every chord** has a no-barre shape. If a
  chord truly needs simplifying, use a short labeled "easier version".
- **Keyboard:** each hand spans no more than about a ninth, right-hand voicings sit mostly G3–G4 under
  the vocal, and the left hand plays bass plus a 5th or octave.
- **Prefer the chord choices that make both of these easy** when choosing between options.

## Technical requirements (Logic Pro)
- Standard MIDI File **Type 1**, 480 PPQ. Track 0 holds tempo, time signature, key signature and
  section markers (`Section name (bars a-b)`). Every track starts at bar 1 and ends exactly on the last
  barline, with no trailing silence.
- **Never write CC7 (volume) or CC10 (pan).** Logic locks its faders to them. CC64 on piano and CC11
  for swells are fine.
- Program changes are labels only. Don't rely on them to choose Logic patches; tell me what to load.
- Humanize timing and velocity lightly, with a fixed seed so files rebuild identically. **Give each
  instrument its own random stream**, so changing one part never shifts another.
- Ritardando or a clean final hit to end. Every instrument lands the last downbeat together.

## Deliverables (in the new folder)
1. `full_song_multitrack.mid`: Tempo & Meter, Grand Piano, Drums, Bass, Rhodes, and Shaker &
   Tambourine (if used), each on its own named track.
2. `piano_only.mid`, `drums_only.mid`, `bass_only.mid`, `rhodes_only.mid`, `aux_percussion_only.mid`,
   each with the same tempo map, aligned to the multitrack.
3. `chord_guide.mid`: plain root-position block chords (bass note alone underneath) for Logic's Chord
   Track detection.
4. `lead_sheet.html`, published as an Artifact, in the same style as the Pancakes lead sheet:
   - the chart by bar: chord symbol, then the piano keyboard diagram for that chord with finger
     numbers, then an empty lyric line for me to fill in, with section marks and band cues
   - then "How to play the chords": one card per chord with the piano voicing (LH/RH, finger numbers)
     and the no-barre guitar diagram (capo, finger numbers, sounding notes)
   - It must work in light and dark themes and at phone width. Tapping a chord jumps to its card.
5. `README_LOGIC.md`: a beginner-friendly guide covering key, tempo, meter, duration, section/bar map,
   chord progressions, track/channel list, what patch to load per track (Steinway Grand Piano, an
   acoustic kit such as Brooklyn or SoCal, a fingerstyle bass, Vintage Electric Piano), how to open the
   file, how to check kick, snare and hat notes, the fallback if a track makes no sound, a note to set
   any bass region Transpose to 0, and how to fill the Chord Track from `chord_guide.mid`.
6. `drum_map.md`: every drum note used, with Logic note names (C1 = 36), velocity conventions, and what
   the drums do in each section.
7. Generator scripts, `chord_shapes.py`, and `validate_arrangement.py`, all reproducible with
   `pip install mido`.
8. A short `README.md` index for the folder.

## Validate before you finish
Reopen every file and check:
- type, track names, channels, programs, and that no CC7 or CC10 is present
- the tempo, meter and key match across all files, and markers sit on the section boundaries
- duration is 3:00–4:00, with no hanging notes and nothing outside the timeline
- drum notes are all in the documented GM map, and bass stays within E1–G3
- bass hits the chord's bass note on every chord change; Rhodes and chord-guide notes are chord tones
- the loudness arc (rule 3), and chorus 1 is smaller than chorus 2
- every guitar shape is barre-free within four frets above the capo, and every keyboard voicing is
  playable
- **originality vs Pancakes**: different key, no four-chord sequence in the same order as any in
  `PANCAKESLEMONADE/pancakes-and-lemonade/generate_piano.py`, a different hook rhythm, a different
  chorus rhythm cell. Write this check as code and run it.
- Render the lead sheet once to check it fits at desktop and phone widths.

Fix any failure before reporting. Then commit with clear messages and push to the branch this session
gives you. Don't open a pull request unless I ask.

## Report back to me
Keep it short and plain:
- folder path, title, key, BPM, duration, capo
- the section/bar map with chords
- the track list
- validation results
- the lead sheet link
- what is verified versus what still needs my ears in Logic
- the 3–4 steps to open it in Logic and hear it

If something can't be done or verified, say so plainly.
