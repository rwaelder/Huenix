import requests
import json
import sys
import os
import difflib

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


path = os.path.dirname(os.path.abspath(__file__))


class App(QMainWindow):

	def __init__(self):
		super().__init__()
		self.left = 10
		self.top = 10
		self.title = 'Huenix Control Panel'
		self.width = 480

		self.get_config()

		self.get_light_groups()

		self.currentState = []

		self.init_UI()

	def init_UI(self):


		self.height = 60 * len(self.lightGroups)
		# if self.height > 500:


		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.setWindowIcon(QIcon( os.path.join(path, 'light-bulb-icon.png') ))


		self.labels = []
		self.sliders = []

		for i, lightGroup in enumerate(self.lightGroups):
			label = QLabel(self)
			label.setAlignment(Qt.AlignRight)
			label.setText( lightGroup )
			
			left = 10
			top = 10 + i * 60
			label.move(left, top)
			label.resize(150, 50)

			self.labels.append(label)

			slider = QSlider(Qt.Horizontal, self)
			slider.setMinimum(0)
			slider.setMaximum(255)

			brightness = self.get_group_brightness(lightGroup)
			self.currentState.append(brightness)

			slider.setValue(brightness)

			slider.sliderReleased.connect(lambda : self.change_group_brightness())

			left = 180
			top = 10 + i * 60
			slider.move(left, top)
			slider.resize(270, 50)

			self.sliders.append(slider)
		

		self.show()
		return

	def error(self, text):
		QMessageBox.question(self, 'Error', text, QMessageBox.Ok)
		sys.exit()

	def api_get(self, apiURL):
		response = requests.get(apiURL)
		

		if response.status_code == 200:
			# responseDict = json.loads(jsonResponse)
			return response.json()

		else:
			messageText = 'Error with API %s' % apiURL
			self.error(messageText)

	def api_put(self, apiURL, data):
		response = requests.put(apiURL, data=data)

		if response.status_code != 200:
			messageText = 'Error with API %s' % apiURL
			self.error(messageText)

	def get_group_brightness(self, groupLabel):
		url = self.urlBase + 'groups/%s' % self.lightGroups[groupLabel]

		response = self.api_get(url)

		if response["action"]["on"] == False:
			brightness = 0
		else:
			brightness = response["action"]["bri"]

		return brightness


	def get_light_groups(self):
		groupsURL = self.urlBase + 'groups'

		response = self.api_get(groupsURL)

		self.lightGroups = {}

		for group in response:
			label = response[group]["name"]
			self.lightGroups[label] = group

	# def change_group_brightness(self, groupNumber, brightness):
	def change_group_brightness(self):

		for i in range(len(self.labels)):
			url = self.urlBase + 'groups/%s/action' % self.lightGroups[self.labels[i].text()]
			brightness = self.sliders[i].value()

			if brightness != self.currentState[i]:

				if brightness == 0:
					data = '{"on":false, "bri":0}'
				else:
					data = '{"on":true, "bri":%i}' % brightness

				response = self.api_put(url, data)

				self.currentState[i] = brightness

	def get_config(self):

		self.config = {}

		self.config['apiKey'] = ''
		self.config['bridgeAddress'] = ''

		confFile = os.path.join(path, 'huenix.conf')

		try:
			with open (confFile, 'r') as f:
				lines = f.readlines()

				for line in lines:
					if 'api_key' in line:
						self.config['apiKey'] = line.split('=')[1].rstrip()

					if 'bridge_ip' in line:
						self.config['bridgeAddress'] = line.split('=')[1].rstrip()

					self.urlBase ='http://%s/api/%s/' % (self.config['bridgeAddress'], self.config['apiKey'])

			if self.config['bridgeAddress'] in ['', '192.168.XXX.XXX']:
				errorText = '''Hue Bridge IP address unspecified, please add bridge IP address to %s 
							To find the Hue Bridge IP address, login to your router, 
							or in the settings menu of the Philips Hue phone app.''' % confFile
				self.error(errorText)

		except IOError:
			with open (confFile, 'w') as f:
				f.write('api_key=Replace me with API key.\n')
				f.write('bridge_address=192.168.XXX.XXX\n')


			errorText = '''No config file found. Created config template %s.
					To obtain a key, follow instructions at developers.meethue.com/develop/get-started-2/ 
					To find the Hue Bridge IP address, login to your router, or in the settings menu of the Philips Hue phone app.''' % confFile
			sys.exit(errorText)







if __name__ == '__main__':

	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())
