ORIGINAL PIANO SONG — piano-only arrangement (working title: untitled)
=====================================================================

Files
  original_piano_song.mid   The MIDI file (Type 1, 480 PPQ)
  generate_piano_song.py    Rebuilds the MIDI (needs: pip install mido)
  validate_midi.py          Reopens the MIDI and checks it

Key       E-flat major (with borrowed chords, and a bridge in G-flat major)
Tempo     96 BPM, straight 16th-note feel. Slows down over the last two bars
          (92 > 90 > 86 > 80 BPM).
Meter     4/4
Length    80 bars, 3:20.5 (tempo 96 for bars 1-78 = 195.0 s, plus 5.5 s of ritardando)

Tracks
  1  "Tempo & Meter"  tempo map, 4/4, key of Eb, section markers
  2  "Grand Piano"    GM program 1 (Acoustic Grand Piano), channel 1. Both hands
                      plus sustain pedal (CC64). Left hand is roughly below C4,
                      right hand above it.

The rhythm
  Verse:   left hand plays the bass note on beat 1 and a push on the "and" of 2.
           Right hand plays short, off-beat chord stabs (the "and" of 1, the
           last 16th of beat 2, and beat 4). This leaves space for a singer.
  Chorus:  right-hand chords in a 3+3+2 / 3+3+2 sixteenth-note pattern, with
           left-hand octaves and a chromatic note leading into each new bass note.
  Hook:    a 5-note figure (two quick 16ths, a held note, then a falling
           answer). It opens the song and comes back in the turnaround,
           breakdown, the quiet part of the last chorus, and the outro.
           It is altered to fit each chord.

Sections (bar numbers) and chords
  Bars  1-4   Intro         Ebmaj9 | Bb/D | Abmaj7/C | Bb9sus4
  Bars  5-12  Verse 1       Ebmaj9 | Bb/D | Cm9 | Cm7/Bb |
                            Abmaj9 | Gm11  C7b9 | Fm9 | Bb9sus4  Bb9
  Bars 13-16  Pre-Chorus 1  Abmaj9 | Am7b5  D7b9 | Gm11  Gb9 | Fm7  Bb9sus4
  Bars 17-24  Chorus 1      Abmaj9 | Bb/Ab | Gm11 | C7b9 |
                            Fm9 | Bb13 | Gm11  Cm7 | Fm7  Bb9sus4
  Bars 25-26  Turnaround    Ebmaj9 | Ab/Bb
  Bars 27-34  Verse 2       same chords as Verse 1, with a busier left hand
  Bars 35-38  Pre-Chorus 2  Abmaj9 | Am7b5  D7b9 | Gm11  Gb9 | Fm9  Bb13
  Bars 39-46  Chorus 2      Abmaj9 | Bb/Ab | Gm11 | C7b9 |
                            Fm9 | Abm6 | Eb/G  Gbdim7 | Fm7  Bb9sus4
  Bars 47-54  Bridge        Cbmaj9 | Db/Cb | Bbm9 | Ebm9 |
              (G-flat major) Abm9 | Db13 | Gbmaj9 | Gbmaj7#11
                            Bars 47-50 are half-time and open, with a high
                            counter-melody. Bars 51-54 climb: right hand in
                            8ths, then 16ths, getting louder.
  Bars 55-56  Breakdown     Abm6 | Bb9sus4  Bb7b9   (drops to quiet, then a
                            16th-note crescendo)
  Bars 57-64  Final Chorus  same chords as Chorus 1, higher and fuller
  Bars 65-72  Final Chorus  same chords as Chorus 2. Bars 65-68 drop back to
              (pull-back)   held chords with the hook on top, then bars 69-72
                            are the loudest part of the song.
  Bars 73-80  Outro         Ebmaj9 | Bb/D | Abmaj7/C | Abm6/Cb |
                            Ebmaj9/Bb | Ab/Bb | Ebmaj9 | Ebmaj9 (held, ritardando)

  Chord changes written "X  Y" in one bar happen on beat 3.
  How loud it gets: the intro and verse 1 average about velocity 55, the
  choruses 82-89, the final chorus 95, and the outro fades to about 45.

Importing into Logic Pro
  Option A (recommended): use File > Open and choose original_piano_song.mid.
    Logic makes a new project and keeps the tempo map (including the
    ritardando), the 4/4 meter, the key, and the section markers.
  Option B: in an existing project, use File > Import > MIDI File... (or drag
    the file into the Tracks area). If Logic asks whether to import the tempo
    information, click Import. Otherwise the ending ritardando and the 96 BPM
    tempo won't come in.
  Logic will make a Software Instrument track called "Grand Piano". If it
  doesn't load a piano by itself, pick one from the Library, e.g. Piano >
  Steinway Grand Piano. The sustain pedal is recorded as CC64, so it plays
  back as written. In the Piano Roll the hands are easy to see either side
  of C4. To split them onto two tracks, select the region and use
  Edit > Separate MIDI Events > By Note Pitch, or split at C4.

Regenerating
  python3 generate_piano_song.py && python3 validate_midi.py
  The random seed is fixed, so you get the same file every time. You can
  change the chords (CH, VERSE, ...), the melody (MEL), the loudness
  (the two numbers on each FORM row), or the seed.

Validation results (validate_midi.py, all PASS)
  Type 1, 2 tracks, 480 PPQ. 4/4 and Eb set at tick 0. Tempo 96 with the
  ritardando at bars 79-80. 1,920 notes, none left hanging, no overlapping
  repeats of the same key. Pitch range Eb1-C#6. Velocity 26-115.
  239 sustain-pedal events. Every bar 1-80 has notes. The first note is at
  tick 0, and the last note ends exactly at the end of bar 80, where both
  tracks also end. Duration 200.53 s. Section markers at bars 1, 5, 13, 17,
  25, 27, 35, 39, 47, 55, 57, 65, 73.

Not verified: the import was not tested in Logic Pro itself, which isn't
available here. The file uses only standard MIDI messages that Logic reads.
Nobody has listened to the result yet; it was checked by analysis only.
