#!/usr/bin/python3

from time import sleep
import json
import re

from minecraft import MinecraftServer
from frozax.freeboxcontroller import FreeboxController
from frozax.log import warning


class Button(object):
    def __init__(self, name, button_id, command, pos):
        self.name = name
        self.id = button_id
        self.command = command
        self.pos = pos


class Remote(object):
    def __init__(self, ms, fbx, conf_base):
        self.fbx = fbx
        self.ms = ms
        self.conf = conf_base["config"]

        self.buttons = []
        large_pos = [0, 0, 0, 0]
        for button_conf in conf_base["buttons"]:
            if "large_pos" in button_conf:
                # if not everything is set, use previous value
                for i, coord in enumerate(button_conf["large_pos"]):
                    large_pos[i] = coord
            button = Button(button_conf["name"], int(button_conf["value"]), button_conf["command"], list(large_pos))
            self.buttons.append(button)

    def press(self, button_id):
        for button in self.buttons:
            if button_id == button.id:
                self.fbx.press(button.command)
                pos_from = list(self.conf["large_pos_top_left"])
                pos_from[2] -= button.pos[0]
                pos_from[1] -= button.pos[1]
                pos_to = list(pos_from)
                pos_to[0] += 1
                pos_to[1] -= button.pos[3]
                pos_to[2] -= button.pos[2]
                lit_blocks = [("stained_hardened_clay", 0), ("stained_hardened_clay", 15)]
                unlit_blocks = [("stained_hardened_clay", 8), ("quartz_block", 0)]
                # light up the remote
                for lit, unlit in zip(lit_blocks, unlit_blocks):
                    self.ms.replace(pos_from, pos_to, lit[0], lit[1], unlit[0], unlit[1])
                sleep(0.5)
                for lit, unlit in zip(lit_blocks, unlit_blocks):
                    self.ms.replace(pos_from, pos_to, unlit[0], unlit[1], lit[0], lit[1])


# class dealing with the variable used to transmit data
class ControlVariable(object):
    def __init__(self, ms):
        self.obj_name = "remote"
        self.ms = ms
        self.ms.set_command_block_output(False)
        self.ms._command("time set 1000")
        self.ms._command("gamerule doDayLightCycle false")
        self.clear()

    def clear(self):
        self.ms._command("gamerule %s 0" % (self.obj_name))

    def get(self):
        output = self.ms._command("gamerule %s" % (self.obj_name))
        # check all lines of output to find the right one
        for line in output:
            match = re.match(".*: %s = ([0-9]+)" % self.obj_name, line)
            if match is not None:
                return int(match.group(1))
        warning("Error reading objective")
        return 0


if __name__ == '__main__':
    minecraft_server = MinecraftServer("fbx")
    control_variable = ControlVariable(minecraft_server)

    freebox_controller = FreeboxController()

    # read config
    conf = json.load(open("conf.json"))
    remote = Remote(minecraft_server, freebox_controller, conf)

    while True:
        v = control_variable.get()
        if v != 0:
            control_variable.clear()
            remote.press(v)
        sleep(0.1)
