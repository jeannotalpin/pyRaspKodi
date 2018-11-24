#!/usr/bin/env python2
from hermes_python.hermes import Hermes
from pykodi.kodi import Kodi


#print('Intent {}'.format(intent_message.intent))
#for (slot_value, slot) in intent_message.slots.items():
#    print('Slot {} -> \n\tRaw: {} \tValue: {}'.format(slot_value, slot[0].raw_value, slot[0].slot_value.value.value))
#hermes.publish_continue_session(intent_message.session_id, "But, prout prout prout or prout?", ["juandelasvacaciones:volumeUp"])
#print "intent name=", intent_message.intent.intent_name


def volumeUpDownReceived(hermes, intent_message):
    """ Increase or decrease volume. If user gives the increment, it is used otherwise a fixed one is used
    """
    inc = 20
    for (slot_value, slot) in intent_message.slots.items():
        inc = int(slot[0].slot_value.value.value)
    direction = "up" if "up" in intent_message.intent.intent_name.lower() else "down"
    newL = kodi.incrementalVolumeChange(direction=direction, increment=inc)
    hermes.publish_end_session(intent_message.session_id, "Done! The sound level is now {}".format(newL))

def playPause(hermes, intent_message):
    """ Toggle player (pause/play)
    Say something in return only if there is no active player
    """
    if kodi.toggle_player():
        text=None
    else:
        text = "Sorry, there is no active player!"
    hermes.publish_end_session(intent_message.session_id, text)

def prevNext(hermes, intent_message):
    """ Go to next or previous song
    """
    intent_name = intent_message.intent.intent_name.lower()
    if "previous" in intent_name:
        direction = "previous"
    elif "next" in intent_name:
        direction = "next"
    else:
        hermes.publish_end_session(intent_message.session_id, "Clarify your intentions!".format(newL))
        return False

    if kodi.goPrevNext(direction=direction):
        text = "Playing {} song.".format(direction)
    else:
        text = "Oops, sorry: something went wrong..."
    hermes.publish_end_session(intent_message.session_id, text)



def allIntent(hermes, intent_message):
    print "intent name=", intent_message.intent.intent_name

host="192.168.1.26"
port=8080
kodi = Kodi(host, port)
with Hermes('localhost:1883') as h:
    #h = h.subscribe_intents(allIntent)
    ## Volume
    h = h.subscribe_intent("juandelasvacaciones:volumeUp", volumeUpDownReceived)
    h = h.subscribe_intent("volumeDown", volumeUpDownReceived)
    ## Play/Pause
    h = h.subscribe_intent("speakerInterrupt", playPause)
    h = h.subscribe_intent("resumeMusic", playPause)
    ## Next/previous
    h = h.subscribe_intent("nextSong", prevNext)
    h = h.subscribe_intent("previousSong", prevNext)
    h.start()





