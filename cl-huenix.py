import requests
import json
import sys
import os
import difflib
import argparse

path = os.path.dirname(os.path.abspath(__file__))

# ---------- Light Functions ------------------

def get_config():

	config = {}

	config['apiKey'] = ''
	config['bridgeAddress'] = ''

	conf_file = os.path.join(path, 'huenix.conf')

	try:
		with open (conf_file, 'r') as f:
			lines = f.readlines()

			for line in lines:
				if 'api_key' in line:
					config['apiKey'] = line.split('=')[1].rstrip()

				if 'bridge_ip' in line:
					config['bridgeAddress'] = line.split('=')[1].rstrip()

			url_base ='http://{ip}/api/{key}/'.format(ip=config['bridgeAddress'], key=config['apiKey'])

		if config['bridgeAddress'] in ['', '192.168.XXX.XXX']:
			errorText = '''Hue Bridge IP address unspecified, please add bridge IP address to {conf} 
						To find the Hue Bridge IP address, login to your router, 
						or in the settings menu of the Philips Hue phone app.'''.format(conf=conf_file)
			error(errorText)

	except IOError:
		with open (conf_file, 'w') as f:
			f.write('api_key=Replace me with API key.\n')
			f.write('bridge_address=192.168.XXX.XXX\n')


		errorText = '''No config file found. Created config template {conf}.
				To obtain a key, follow instructions at developers.meethue.com/develop/get-started-2/
				To find the Hue Bridge IP address, login to your router, 
				or in the settings menu of the Philips Hue phone app.'''.format(conf=conf_file)
		error(errorText)

	return url_base

def get_groups(url_base):
	api_url = url_base + 'groups'

	response = api_get(api_url)

	light_groups = []

	for group in response:
		current_group = {}

		current_group["label"] = response[group]["name"]
		current_group["state"] = response[group]["action"]

		light_groups.append(current_group)

	return light_groups

# ---------- API Functions --------------------
def api_get(api_url):
	response = requests.get(api_url)

	if response.status_code == 200:
		return response.json()

	else:
		api_error(api_url, response.status_code)

def api_put(api_url, data):
	data = json.dumps(data)

	response = requests.put(api_url, data=data)

	if response.status_code != 200:
		api_error(api_url, response.status_code)


# ---------- Interface Functions --------------

def fatal_error(error_message):
	print('\n')
	print(error_message)
	print('\n')

	sys.exit()

def interactive_error(error_message):
	print('\n')
	print(error_message)
	print('\n')

def api_error(api_url, status_code):
	print('\n')
	print('API error {status_code}'.format(status_code=status_code))
	print(api_url)
	print('\n')

	sys.exit()


def print_status(url_base):

	light_groups = get_groups(url_base)

	print('\n')

	print('{:12} | {:5} | {:12} | {:12} | {:7}'.format(
		'Group', 'State', 'Brightness', 'Saturation', 'Color'))

	group_numbers = {}

	for group in light_groups:

		label = group['label']

		if group['state']['on']:
			state = 'on'
		else:
			state = 'off'

		brightness = group['state']['bri']

		try:
			saturation = group['state']['sat']
		except KeyError:
			saturation = 'N/A'

		try:
			color = group['state']['hue']
		except KeyError:
			color = 'N/A'
		

		print('{:<12.12} | {:<5} | {:<12} | {:<12} | {:<7}'.format(
		label, state, brightness, saturation, color))

	print('\n')


def print_help():

	print('\n')
	print('----- Help Menu ----------')
	print('\n')
	print('Commands are parsed with the exception of the light group.')
	print('The light group must be the first word in the command.')
	print('Except for on/off, which can be specified as \"on\" or \"off\",')
	print('commands must specify the variable label before the value.')

	print('\n')
	print('Groups: Exclude any spaces in group names')
	print('\t specifying \"all\" will control all light groups.')
	print('State: Either \"on\" or \"off\".')
	print('Brightness: integer from 0 to 254')
	print('Saturation: integer from 0 to 254')
	print('\t 0 is least saturated (white), 254 is most colored.')
	print('Color: wrapping integer from 0 to 65535.')
	print('\t 0 and 65535 are red, 25500 is green, 46920 is blue.')

	print('\n')
	print('Keywords can be specified in long or short form (first three letters)')
	print('\n')
	print('Example command: livingroom on brightness 254 col 0 sat 254')

	print('\n\n')


def parse_command(command, url_base):

	groups = get_groups(url_base)
	group_nums = {}
	for i, group in enumerate(groups):
		label = group["label"].lower().replace(' ', '')

		group_nums[label] = i+1


	command_parts = command.split(' ')

	if command_parts[0].lower() == 'all':
		group_num = 0
	else:

		try:
			group_num = group_nums[ difflib.get_close_matches(command_parts[0], list(group_nums.keys()))[0] ]
		except KeyError:
			interactive_error('Specified group not found')
			return None, None

	api_url = url_base + 'groups/{:d}/action'.format(group_num)



	action = {}
	for i, part in enumerate(command_parts):

		if part.lower() in ['on', 'off']:
			if part.lower() == 'on':
				action["on"] = True
			else:
				action["on"] = False

		elif part.lower() in ['bri', 'brightness']:
			try:
				val = int(command_parts[i+1])

				if val > 254:
					val = 254
				elif val < 0:
					val = 0

				action["bri"] = val

			except ValueError:
				error('Specified brightess value not interpretable.')
				return None, None
			except IndexError:
				error('Brightness value not specified.')
				return None, None

		elif part.lower() in ['sat', 'saturation']:
			try:
				val = int(command_parts[i+1])
				
				if val > 254:
					val = 254
				elif val < 0:
					val = 0

				action["sat"] = val

			except ValueError:
				error('Specified saturation value not interpretable.')
				return None, None
			except IndexError:
				error('Saturation value not specified.')
				return None, None

		elif part.lower() in ['col', 'color']:
			try:
				val = int(command_parts[i+1])
				
				if val > 65535:
					val = 65535
				elif val < 0:
					val = 0

				action["hue"] = val

			except ValueError:
				error('Specified color value not interpretable.')
				return None, None
			except IndexError:
				error('Color value not specified.')
				return None, None

	return api_url, action

# ---------- Main -----------------------------

def one_liner(args):

	url_base = get_config()

	if args.print and not args.group:
		print_status(url_base)
		return
	
	if not args.group:
		fatal_error('No light(s) specified. Specify light(s) with -g')

	if args.group and not args.onoff and not args.brightness and not args.color and not args.saturation:
		fatal_error('No command specified')



	

	groups = get_groups(url_base)

	group_nums = {}
	for i, group in enumerate(groups):
		label = group["label"].lower().replace(' ', '')

		group_nums[label] = i+1


	if args.group.lower() == 'all':
		group_num = 0
	else:

		try:
			group_num = group_nums[ difflib.get_close_matches(args.group, group_nums.keys())[0] ]
		except KeyError:
			interactive_error('Specified group not found')
			return None, None

	api_url = url_base + 'groups/{:d}/action'

	action = {}

	if args.onoff:
		if args.onoff.lower() == 'on':
			action["on"] = True
		elif args.onoff.lower() == 'off':
			action["on"] = False
		else:
			fatal_error('Invalid on/off state specified.')

	if args.brightness:
		if args.brightness > 254:
			brightness = 254
		elif args.brightness < 0:
			brightness = 0
		else:
			brightness = args.brightness

		action["bri"] = brightness

	if args.saturation:
		if args.saturation > 254:
			saturation = 254
		elif args.saturation < 0:
			saturation = 0
		else:
			saturation = args.saturation

		action["sat"] = saturation

	if args.color:
		if args.color > 65535:
			color = 65535
		elif args.color < 0:
			color = 0
		else:
			color = args.color

		action["hue"] = color

	if args.print:
		api_put(api_url, action)
		print_status(url_base)
	else:
		api_put(api_url, action)



def interactive():
	url_base = get_config()

	print_status(url_base)

	quit = False
	while not quit:
		command = input('Enter command or one of status, help, quit:\n').rstrip()

		if command.lower() == 'status':
			print_status(url_base)

		elif command.lower() == 'help':
			print_help()

		elif command.lower() == 'quit':
			quit = True

		else:
			api_url, action = parse_command(command, url_base)
			if action is not None:

				api_put(api_url, action)

				print_status(url_base)




if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		description='command-line Phillips Hue tool')

	parser.add_argument('-g', '--group', type=str, 
		help='label of light group for one-liner usage')
	parser.add_argument('-b', '--brightness', type=int,
		help='set brightness value for specified light(s)')
	parser.add_argument('-o', '--onoff', type=str,
		help='set state (on/off) of specified light(s)')
	parser.add_argument('-c', '--color', type=int,
		help='set color of specified light(s)')
	parser.add_argument('-s', '--saturation', type=int,
		help='set saturation of specified light(s)')
	parser.add_argument('-p', '--print',
		help='print current state of all lights/groups')

	args = parser.parse_args()

	if len(sys.argv) > 1:
		one_liner(args)

	else:
		interactive()

	sys.exit()