#/usr/bin/env python2
import requests
import json
import logging


#class Error(Exception):
#    """Base error class"""
#    pass
#
#class GetError(Error):
#    """Error raised when GET returns a code != 200"""
#    def __init__(self, expression, message):
#        self.expression = expression
#        self.message = message
#
#class NoActivePlayer(Error):
#    def __init__(self, message="There is no active player on Kodi"):
#        self.message = message


class Kodi(object):
    def __init__(self, host, port, logger = None):
        self.address="http://%s:%i/jsonrpc?request=" %(host, int(port))
        self.data = {
                "jsonrpc" : "2.0",
                "id" : 1,
                "method" : None, ## to be added for action
                "params" : {}, ## same
                }
        if logger is None:
            self.logger = logging.getLogger()
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Starting logging")
        else:
            self.logger = logger
                


    def send(self, data):
        """ Send a GET request to Kodi """
        req = "%s%s" %(self.address, json.dumps(data))
        #self.logger.debug("Sending request with req=%s\n%s" %(req, json.dumps(data, indent=2)))
        #self.logger.debug("Sending request with req=%s\n" %(req,))
        resp = requests.get(req)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ValueError('GET returned {}'.format(resp.status_code))
        return resp.json()

    def get_active_player(self):
        """ Get the active player """
        data = self.data.copy()
        data["method"]= "Player.GetActivePlayers" 
        js = self.send(data)
        if len(js["result"])>0:
            for player in js["result"]:
                if player["type"] == "audio" or player["type"] == "video":
                    return js["result"][0] ## [{u'playerid': 0, u'type': u'audio'}]
        else:
            self.logger.warning("There is no active player")
        return []

    def toggle_player(self):
        """ Unpause the music if the player is paused or pause it if it is playing
        Do nothing if no active player is found
        return true if the toggle happened, False if it failed (to be used for a voice feedback)
        """
        player = self.get_active_player()
        if player != []:
            data = self.data.copy()
            data["method"] = "Player.PlayPause" 
            data["params"] = {"playerid":player["playerid"]}
            js = self.send(data)
            toreturn = True
            self.logger.debug("Successfully tooggled")
        else:
            #logger.warning("There is no active player")
            toreturn = False
        return toreturn

    def stop_player(self):
        """ Stop the music 
        Do nothing if no active player is found
        return true if the stop happened, False if it failed (to be used for a voice feedback)
        """
        player = self.get_active_player()
        if player != []:
            data = self.data.copy()
            data["method"] = "Player.Stop" 
            data["params"] = {"playerid":player["playerid"]}
            js = self.send(data)
            toreturn = True
            self.logger.debug("Successfully stopped")
        else:
            logger.warning("There is no active player")
            toreturn = False
        return toreturn

    def incrementalVolumeChange(self, direction="up", increment=20):
        """ Increment or decrement the volume, based on current level """
        ## Get current level
        data=self.data.copy()
        data["method"] = "Application.GetProperties"
        data["params"] = {"properties":["volume"]}
        js = self.send(data)
        curlevel = int(js["result"]["volume"])
        self.logger.debug("Current sound level is %i"%curlevel)
        newlevel = min(100, curlevel+increment) if direction=="up" else max(10, curlevel-increment)
        data = self.data.copy()
        data["method"] = "Application.SetVolume"
        data["params"] = {"volume":newlevel}
        js = self.send(data)
        returnedLevel = int(js["result"])
        self.logger.debug("New sound level is %i"%returnedLevel)
        return returnedLevel

    def goPrevNext(self, direction="next"):
        """ Go to the next song (direction="next") or the previous one (direction="previous")
        return True or False depending on the success
        """
        player = self.get_active_player()
        if player != []:
            data = self.data.copy()
            data["method"] = "Player.GoTo" 
            data["params"] = {
                    "playerid":player["playerid"],
                    "to" : direction
                }
            js = self.send(data)
            if js["result"] == "OK":
                toreturn = True 
                self.logger.debug("Successfully switched")
            else :
                toreturn = False
                self.logger.warning("There has been a problem while switching: {}".format(js["result"]))
        else:
            #logger.warning("There is no active player")
            toreturn = False
        return toreturn

    def getSongs(self):
        """ Find all songs
        """
        data=self.data.copy()
        data["method"] = "AudioLibrary.GetSongs"
        data["params"] = {}
        js = self.send(data)
        for s in js["result"]["songs"]:
            print s["label"]
            if "quitte pas" in s["label"]:
                print "Found!"
                sys.exit()


        


if __name__ == "__main__":

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


    kod = Kodi("192.168.1.26", 8080, logger)
    #print kod.toggle_player()
    #print kod.stop_player()
    #print kod.incrementalVolumeChange("up")
    kod.getSongs()
