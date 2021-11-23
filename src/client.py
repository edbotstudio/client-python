#
# A Python client API for Edbot Studio.
#
# Copyright (c) Robots in Schools Ltd. All rights reserved.
#

import json
import time
import threading

from pydash.objects import merge, unset
from ws4py.client.threadedclient import WebSocketClient

class EdbotStudioClient(WebSocketClient):
	Category = {
		"REQUEST": 1,
		"RESPONSE": 2,
		"UPDATE": 3,
		"DELETE": 4,
		"CLOSE": 5
	}
	Type = {
		"INIT": 1,
		"GET_CLIENTS": 2,
		"GET_SERVERS": 3,
		"GET_SENSORS": 4,
		"GET_SERVOS": 5,
		"RUN_MOTION": 6,
		"SET_SERVOS": 7,
		"SET_SPEAKER": 8,
		"SET_DISPLAY": 9,
		"SET_OPTIONS": 10,
		"SET_CUSTOM": 11,
		"SAY": 12, 
		"RESET": 13
	}

	def __init__(self, server="localhost", port=54255, listener=None, name=None,
			reporters=True, device_alias=None):
		self.server = server
		self.port = port
		self.listener = listener
		self.name = name
		self.reporters = reporters
		self.device_alias = device_alias
		self.connected = False
		self.sequence = 1
		self.opened_event = threading.Event()
		self.pending = {}

	def connect(self, callback=None):
		if self.connected:
			return									# silently return
		url = "ws://{}:{}/api".format(self.server, self.port)
		WebSocketClient.__init__(self, url)
		WebSocketClient.connect(self)
		t = threading.Thread(target=self.run_forever)
		t.setDaemon(True)
		t.start()

		#
		# Wait for the opened() callback. If things went wrong the previous
		# call to WebSocketClient.connect() should have raised an exception.
		#
		self._wait(self.opened_event)

		# Initialise the data dictionary.
		self.data = {}
	
		# Send the INIT request.
		params = {
			"name": self.name,
			"reporters": self.reporters,
			"deviceAlias": self.device_alias
		}
		self._send(EdbotStudioClient.Type["INIT"], params, callback)

	###########################################################################

	def opened(self):
		self.opened_event.set()

	def received_message(self, m):
		message = json.loads(m.data.decode("UTF-8"))
		if message["category"] == EdbotStudioClient.Category["RESPONSE"]:
			#
			# Run code specific to the response message type.
			#
			if message["type"] == EdbotStudioClient.Type["INIT"]:
				merge(self.data, message["data"])
				self.connected = True
				if self.listener is not None:
					self.listener(message)

			#
			# Use the sequence as a key in the pending dictionary. There
			# will either be a callback to trigger or an event to resolve.
			#
			sequence = message["sequence"]
			pending = self.pending[sequence]
			callback = pending["callback"]
			if callback is not None:
				if message["status"]["success"]:
					callback(True, { "data": message["data"] })
				else:
					callback(False, { "data": message["status"]["text"] })
				del self.pending[sequence]
			else:
				self.pending[sequence]["response"] = message
				event = pending["event"]
				event.set()
		elif message["category"] == EdbotStudioClient.Category["UPDATE"]:
			if self.connected:
				merge(self.data, message["data"])
				if self.listener is not None:
					self.listener(message)
		elif message["category"] == EdbotStudioClient.Category["DELETE"]:
			if self.connected:
				unset(self.data, message["data"]["path"])
				if self.listener is not None:
					self.listener(message)

	def closed(self, code, reason=None):
		self.connected = False
		self.data.clear()
		if self.listener is not None:
			self.listener({
				"category": EdbotStudioClient.Category["CLOSE"],
				"data": {
					"code": code,
					"reason": reason
				}
			})

	###########################################################################

	def get_connected(self):
		return self.connected

	#
	# If connected, this will close the connection and call the closed
	# handler. If the connection is already closed, it does nothing.
	#
	def disconnect(self):
		WebSocketClient.close(self, code=1000, reason="Closed by client")

	def get_data(self):
		if not self.connected:
			raise Exception("Not connected")
		return self.data

	def get_robot_names(self, model=None):
		if not self.connected:
			raise Exception("Not connected")
		if model is None:
			return list(self.data["robots"].keys())
		else:
			result = []
			for name in self.data["robots"].keys():
				if self.data["robots"][name]["model"]["type"] == model:
					result.append(name)
			return result

	def get_robot(self, name):
		if not self.connected:
			raise Exception("Not connected")
		if not name in self.data["robots"]:
			raise Exception(name + " is not configured")
		else:
			return self.data["robots"][name]

	def have_control(self, name):
		robot = self.get_robot(name)
		return robot["control"] == self.data["session"]["device"]["id"]

	def await_control(self, name):
		robot = self.get_robot(name)
		while not self.have_control(name):
			time.sleep(0.1)

	def get_clients(self, callback=None):
		return self._request(EdbotStudioClient.Type["GET_CLIENTS"], None, callback)

	def get_servers(self, callback=None):
		return self._request(EdbotStudioClient.Type["GET_SERVERS"], None, callback)

	def get_sensors(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["GET_SENSORS"], params, callback)

	def get_servos(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["GET_SERVOS"], params, callback)

	def run_motion(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["RUN_MOTION"], params, callback)

	def set_servos(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["SET_SERVOS"], params, callback)

	def set_speaker(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["SET_SPEAKER"], params, callback)

	def set_display(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["SET_DISPLAY"], params, callback)

	def set_options(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["SET_OPTIONS"], params, callback)

	def set_custom(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["SET_CUSTOM"], params, callback)

	def say(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["SAY"], params, callback)

	def reset(self, params, callback=None):
		return self._request(EdbotStudioClient.Type["RESET"], params, callback)

	###########################################################################

	def _request(self, type, params, callback):
		if not self.connected:
			raise Exception("Not connected")
		return self._send(type, params, callback)

	def _send(self, type, params, callback):
		with threading.Lock():
			sequence = self.sequence
			self.sequence += 1

			if callback is not None:
				self.pending[sequence] = { "callback": callback, "event": None }
			else:
				self.pending[sequence] = { "callback": None, "event": threading.Event() }

			self.send(
				json.dumps({
					"category": EdbotStudioClient.Category["REQUEST"],
					"type": type,
					"sequence": sequence,
					"params": params
				})
			)
			if callback is None:
				pending = self.pending[sequence]
				self._wait(pending["event"])
				del self.pending[sequence]
				message = pending["response"]
				if message["status"]["success"]:
					return message["data"]
				else:
					raise Exception(message["status"]["text"])

	def _wait(self, event):
		#
		# The function wait() without a timeout isn't interruptible on Windows.
		# Use this workaround until the Python team sort it.
		#
		while not event.wait(0.1):
			pass