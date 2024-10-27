#!/usr/bin/python3
# All software written by Tomas. (https://github.com/shelbenheimer/ata-shell)

from scapy.all import ARP, srp, Ether, get_if_addr, conf
import sys
import importlib
import os
import json
import time

HELP = """SCAN - Scans the network for connected devices."""

BANNER = "Software written by Tomas. Available on GitHub. (https://github.com/shelbenheimer/ata-shell)"
VENDOR_PATH = "/Resources/manuf.json"

TITLE = 'discovery'

TARGET_FLAG = "-t"
INTERFACE_FLAG = "-i"

REQUIRED = [ TARGET_FLAG, INTERFACE_FLAG ]
CONFIGURABLE = [ TARGET_FLAG, INTERFACE_FLAG ]

class Discovery:
	def __init__(self):
		self.address = get_if_addr(conf.iface)
		self.target = self.ResolveCIDR()

		self.path    = f"{os.path.dirname(os.path.abspath(__file__))}{VENDOR_PATH}"
		self.vendors = {}

	def GetHosts(self):
		packet = Ether(dst="FF:FF:FF:FF:FF:FF") / ARP(pdst=self.target)
		replies = srp(packet, timeout=2, verbose=False)[0]

		if not replies: return []

		hosts = []
		for reply in range(0, len(replies)):
			information = (replies[reply][1].psrc, replies[reply][1].hwsrc)
			hosts.append(information)
		return hosts

	def ResolveCIDR(self):
		mask = "255.255.255.0"

		split_mask = mask.split('.')
		split_addr = self.address.split('.')
		counted = 0
		for octet in range(0, len(split_mask)):
			if split_mask[octet] == "0": split_addr[octet] = "0"

			binary = bin(int(split_mask[octet]))[2:]
			for digit in binary:
				if digit == '1': counted += 1

		result = f"{".".join(split_addr)}/{counted}"
		return result

	def PopulateVendors(self):
		try:
			with open(self.path, 'r', encoding="utf8") as file:
				self.vendors = json.load(file)
				return True
		except Exception as error:
			print(error)
			return False

	def FormatOUI(self, address):
		formatted = address[:8].replace("-", ":")
		return formatted

	def GetVendor(self, address):
		if not self.vendors:
			self.vendors = self.PopulateVendors()
		if not self.vendors:
			return "Unobtainable"

		formatted = self.FormatOUI(address).upper()
		try:
			return self.vendors[formatted]
		except:
			return "Unknown Vendor"

def HandleCommand(command, shell):
	match command:
		case 'scan':
			Main(shell)
	shell.buffer = None

def Main():
	try:
		discovery = Discovery()
		print(BANNER)

		if not discovery.PopulateVendors():
			print("Failed to populate manufacturer database.")

		start_time = time.time()
		hosts = discovery.GetHosts()
		if not hosts:
			print("There was an error whilst attempting to scan the network.")
			return

		for host in hosts:
			vendor = discovery.GetVendor(host[1])
			print(f"{host[0]:<18} {host[1]:<20} {vendor:<20}")

		elapsed = time.time() - start_time
		formatted_elapsed = "".join(list(str(elapsed))[:5])
		print(f"Finished scan in {formatted_elapsed}s on {time.ctime()}.")
	except Exception as error:
		print(error)
		return

def Initialise():
	try:
		shell_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		sys.path.append(shell_path)
		library = importlib.import_module('shell')

		shell = library.Shell(TITLE, dialogue=HELP, standalone=True)
		shell.Spawn()

		while shell.active:
			shell.UpdateShell()

			if shell.buffer:
				HandleCommand(shell.buffer, shell)
		shell.Kill()
	except Exception as error:
		print(error)
		return

Main()