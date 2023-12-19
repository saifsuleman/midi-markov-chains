import mido
import random
from collections import defaultdict

def generate_markov_chains(file):
    track_instruments = []
    track_transitions = []

    mid = mido.MidiFile(file)

    current_instrument = None
    current_volume = None

    for track in mid.tracks:
        transitions = defaultdict(lambda: defaultdict(int))
        note_start_times = {}
        last_state = None
        elapsed_time = 0

        for msg in track:
            elapsed_time += msg.time

            if not msg.is_meta:
                if msg.type == "program_change":
                    current_instrument = msg.program
                elif msg.type == "control_change" and msg.control == 7:
                    current_volume = msg.value
                elif msg.type == "note_on" and msg.velocity > 0:
                    note_start_times[msg.note] = elapsed_time, msg.velocity
                elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                    if msg.note in note_start_times:
                        start_time, velocity = note_start_times[msg.note]
                        duration = elapsed_time - start_time

                        if duration < 0:
                            raise Exception(f"Negative duration resolved - msg.time: {msg.time} | note start time: {note_start_times[msg.note]}")

                        current_state = (msg.note, velocity, duration)
                        if last_state is not None:
                            transitions[last_state][current_state] += 1
                        last_state = current_state
                        del note_start_times[msg.note]

        track_transitions.append(transitions)
        track_instruments.append((current_instrument, current_volume))

    return track_transitions, track_instruments

def generate_melodies(markov_chains, length):
    melodies = []

    for chain in markov_chains:
        if not chain:
            continue

        start_state = random.choice(list(chain.keys()))
        melody = [start_state]

        for _ in range(length - 1):
            next_states = chain[melody[-1]]

            if not next_states:
                continue
                # raise Exception("cannot find next_notes for previous note: " + str(melody[-1]))

            next_state = random.choices(list(next_states.keys()), weights=next_states.values())[0]

            if not next_state:
                # raise Exception("cannot find next_note for previous note: " + str(melody[-1]))
                continue

            melody.append(next_state)

        melodies.append(melody)

    return melodies

def create_midi_from_melodies(melodies, instruments, filename):
    mid = mido.MidiFile()

    for channel, (melody, iv) in enumerate(zip(melodies, instruments)):
        instrument, volume = iv
        track = mido.MidiTrack()

        if instrument is not None:
            track.append(mido.Message("program_change", channel=channel, program=instrument, time=0))

        if volume is not None:
            track.append(mido.Message("control_change", channel=channel, control=7, value=volume, time=0))

        for note, velocity, time in melody:
            track.append(mido.Message('note_on', note=note, channel=channel, velocity=velocity, time=0))
            track.append(mido.Message('note_off', note=note, channel=channel, velocity=velocity, time=time))

        mid.tracks.append(track)


    mid.save(filename)

transitions, instruments = generate_markov_chains("samples/rick.mid")
melodies = generate_melodies(transitions, length=200)
create_midi_from_melodies(melodies, instruments, 'output.mid')
