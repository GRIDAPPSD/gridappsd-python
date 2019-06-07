import json
import sys
import time

from . topics import simulation_input_topic, simulation_output_topic, simulation_log_topic


class Simulation(object):
    def __init__(self, gapps, simulation_id: str, duration: int, timestep_finished=None):
        self.gappsd = gapps
        self.simulation_id = simulation_id
        self._show_timesteps = True
        self._duration = int(duration)
        self._timestep_requested = 0
        self._timestep_finished_callback = timestep_finished
        self.gappsd.subscribe(simulation_log_topic(simulation_id), self._on_message)

    def _on_message(self, headers, message):
        if 'logMessage' in message:
            log_message = message['logMessage']
            if log_message.startswith("done with timestep"):
                timestep = int(log_message[len("done with timestep "):])
                if self._timestep_finished_callback is not None:
                    self._timestep_finished_callback(self, timestep)

        if self._show_timesteps:
            # print(headers, message)
            # print(headers)
            sys.stdout.write(f"{message['logMessage']}\n")
            # print(message["logMessage"])

    @property
    def running(self):
        return self.is_running()

    @property
    def showing_status(self):
        return self._show_timesteps

    def pause(self):
        """Pause simulation"""
        command = dict(command="pause")
        self.gappsd.send(simulation_input_topic(self.simulation_id), json.dumps(command))

    def stop(self):
        """Stop the simulation"""
        command = dict(command="stop")
        self.gappsd.send(simulation_input_topic(self.simulation_id), json.dumps(command))

    def resume(self):
        """Resume the simulation"""
        command = dict(command="resume")
        self.gappsd.send(simulation_input_topic(self.simulation_id), json.dumps(command))

    def is_running(self):
        """Find out if the simulation is running or not."""
        print("Running")

    def simulation_main_loop(self):

        while self._timestep_requested < self._duration:
            time.sleep(0.1)
        #
        # import time
        # from curses import wrapper
        #
        # def main(stdscr):
        #     # Clear screen
        #     stdscr.clear()
        #
        #     # # This raises ZeroDivisionError when i == 10.
        #     # for i in range(0, 11):
        #     #     v = i - 10
        #     #     stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10 / v))
        #     while True:
        #         stdscr.refresh()
        #         ch = stdscr.getch() #.getkey()
        #
        #         if chr(ch) == 'q':
        #             return
        #         print("CH is : {}".format(ch))
        #         time.sleep(0.1)
        #
        # wrapper(main)
        #
        # import sys, termios, tty, os, time
        #
        # def getch():
        #     fd = sys.stdin.fileno()
        #     old_settings = termios.tcgetattr(fd)
        #     try:
        #         tty.setraw(sys.stdin.fileno())
        #         ch = sys.stdin.read(1)
        #
        #     finally:
        #         termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        #     return ch
        #
        # button_delay = 0.2
        #
        # while True:
        #     char = getch()
        #
        #     if char == "p":
        #         self.pause()
        #         time.sleep(button_delay)
        #
        #     if char == 'q':
        #         self.stop()
        #         return
        #
        #     if char == 'r':
        #         self.resume()
        #         time.sleep(button_delay)
        #
        #     if char == 'h':
        #         self._show_timesteps = not self._show_timesteps
        #         time.sleep(button_delay)
        #
        #
        #     if (char == "a"):
        #         print("Left pressed")
        #         time.sleep(button_delay)
        #
        #     elif (char == "d"):
        #         print("Right pressed")
        #         time.sleep(button_delay)
        #
        #     elif (char == "w"):
        #         print("Up pressed")
        #         time.sleep(button_delay)
        #
        #     elif (char == "s"):
        #         print("Down pressed")
        #         time.sleep(button_delay)
        #
        #     elif (char == "1"):
        #         print("Number 1 pressed")
        #         time.sleep(button_delay)