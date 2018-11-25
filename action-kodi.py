#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
from pykodi.kodi import Kodi
import io

CONFIG_INI = "config.ini"

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

VOCABULARY = {
        "doneSoundLevel":{
            "fr":u"C'est fait. Le son est maintenant a {}",
            "gb":"Done! The sound level is now {}"
            },
        "noActivePlayer":{
            "fr":u"Désolé, il n'y a pas de lecteur actif.",
            "gb":"Sorry, there is no active player!"
            },
        "clarify":{
            "fr":u"Clarifie tes intentions !",
            "gb":"Clarify your intentions!"
            },
        "previous":{
            "fr":u"Je reviens à la précédente...",
            "gb":"Coming back..."
            },
        "next":{
            "fr":u"Je passe à la suivante",
            "gb":"Playing next song"
            },
        "oops":{
            "fr":u"Oula, je n'ai pas pu faire cette action. Pardon maitre !",
            "gb":"Oops, sorry: something went wrong..."
            },
        "unknown":{
            "fr":u"Je ne connais pas cette intention : {}.",
            "gb": "I don't know this intent: {}"
            }
        }




class Template(object):
    """Class used to wrap action code with mqtt connection
        
        Please change the name refering to your application
    """

    def __init__(self):
        # get the configuration if needed
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except :
            self.config = None

        ## Prepare Kodi
        host = self.config.get("secret").get("kodihost")
        port = int(self.config.get("secret").get("kodiport"))
        self.kodi = Kodi(host, port)

        ## Language
        self.lang = self.config.get("secret").get("lang")
        self.vocal = {}
        for v in VOCABULARY:
            self.vocal[v] = VOCABULARY[v][self.lang]

        # start listening to MQTT
        self.start_blocking()
        

    def intent_volumeUpDownReceived(self, hermes, intent_message):
        """ Increase or decrease volume. If user gives the increment, it is used otherwise a fixed one is used
        """
        inc = 20
        for (slot_value, slot) in intent_message.slots.items():
            inc = int(slot[0].slot_value.value.value)
        direction = "up" if "up" in intent_message.intent.intent_name.lower() else "down"
        newL = self.kodi.incrementalVolumeChange(direction=direction, increment=inc)
        hermes.publish_end_session(intent_message.session_id, self.vocal["doneSoundLevel"].format(newL))

    def intent_playPause(self, hermes, intent_message):
        """ Toggle player (pause/play)
        Say something in return only if there is no active player
        """
        if self.kodi.toggle_player():
            text=None
        else:
            text = self.vocal["noActivePlayer"]
        hermes.publish_end_session(intent_message.session_id, text)

    def intent_prevNext(self, hermes, intent_message):
        """ Go to next or previous song
        """
        intent_name = intent_message.intent.intent_name.lower()
        if "previous" in intent_name:
            direction = "previous"
        elif "next" in intent_name:
            direction = "next"
        else:
            hermes.publish_end_session(intent_message.session_id, self.vocal["clarify"])

            return False

        if self.kodi.goPrevNext(direction=direction):
            text = self.vocal["previous"] if "previous" in direction else self.vocal["next"]
        else:
            text = self.vocal["oops"]
        hermes.publish_end_session(intent_message.session_id, text)

    def intent_unknown(self, hermes, intent_message):
        hermes.publish_end_session(intent_message.session_id, self.vocal["unknown"].format(intent_message.intent.intent_name.lower()))

    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self, hermes, intent_message):
        coming_intent = intent_message.intent.intent_name
        if "volumeup" in coming_intent.lower() or "volumedown" in coming_intent.lower():
            self.intent_volumeUpDownReceived(hermes, intent_message)
        if "speakerinterrupt" in coming_intent.lower() or "resumemusic" in coming_intent.lower():
            self.intent_playPause(hermes, intent_message)
        if "nextsong" in coming_intent.lower() or "previoussong" in coming_intent.lower():
            self.intent_prevNext(hermes, intent_message)
        else:
            self.intent_unknown(hermes, intent_message)


        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

if __name__ == "__main__":
    Template()
