# Originally by an anonymous Discorder

ENGINE = "C:\\Programs (self-installed)\\lc0-cuda\\lc0.exe"
NETWORKS = "C:\\Users\\Owner\\Documents\\Misc\\Chess\\Lc0_Networks"

DEFAULT_FEN = "Q7/Q7/8/6pk/5n2/8/1q6/7K w - - 0 1"
DEFAULT_MOVE = "a8f3"
DEFAULT_STEP = 100

import os, subprocess, sys
import requests
from matplotlib import pyplot as plt

lczero_nets = [None, dict(), dict(), dict()]		# for runs 1, 2, 3


class NetNotKnown(Exception):
	pass


class Engine:

	def __init__(self, engine_location):
		self.process = subprocess.Popen(engine_location, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
		self.send("uci")
		while "uciok" not in self.readline():
			pass
		self.setoption("VerboseMoveStats", True)

	def quit(self):
		self.process.terminate()

	def readline(self):
		return self.process.stdout.readline().decode("utf8").strip()

	def send(self, s):
		s = s.strip() + "\n"
		self.process.stdin.write(s.encode("utf8"))
		self.process.stdin.flush()

	def setoption(self, name, value):
		if value == True:
			value = "true"
		if value == False:
			value = "false"
		self.send(f"setoption name {name} value {value}")

	def test(self, fen, move, net):

		print(net, end=" ", flush=True)
		if not os.path.exists(os.path.join(NETWORKS, f"{net}.pb.gz")):
			dl_net(net)

		self.setoption("WeightsFile", os.path.join(NETWORKS, f"{net}.pb.gz"))
		self.send("ucinewgame")
		self.send(f"position fen {fen}")
		self.send("isready")
		while "readyok" not in self.readline():
			pass
		self.send("go nodes 1")

		policy = None
		value = None

		while True:
			line = self.readline()
			if f"info string {move}" in line:
				policy = float(line.split("(P:")[1].split("%")[0])
			if "info string node" in line:
				value = float(line.split("(V:")[1].split(")")[0])
			if policy != None and value != None:
				break

		print(f"P = {policy} V = {value}")
		return policy, value


def infer_run(net):

	if net >= 60000 and net < 70000:
		return 1

	if net >= 700000 and net < 710000:
		return 2

	if net >= 710000 and net < 720000:
		return 3

	if net >= 720000 and net < 750000:
		return 2

	return None


def dl_inventory(run):

	global lczero_nets

	webtext = requests.get(f"https://training.lczero.org/networks/{run}?show_all=1").text
	lines = webtext.split("\n")

	for line in lines:
		if '<td><a href="/get_network?sha=' in line:
			sha = line.split("sha=")[1].split('"')[0]
			net = line.split(".pb.gz")[0].split("_")[-1]
			lczero_nets[run][int(net)] = sha


def dl_net(net):

	global lczero_nets

	run = infer_run(net)

	if len(lczero_nets[run]) == 0:
		dl_inventory(run)

	try:
		sha = lczero_nets[run][net]
	except:
		raise NetNotKnown

	print(f"(downloading {sha[:8]})", end=" ", flush=True)

	with open(os.path.join(NETWORKS, f"{net}.pb.gz"), "wb") as outfile:
		outfile.write(requests.get(f"https://training.lczero.org/get_network?sha={sha}").content)


def interrogate_user():

	lowest = int(input("Lowest net?  "))

	highest = int(input("Highest net?  "))

	try:
		step = int(input("Step? (leave blank for default)  "))
	except:
		step = DEFAULT_STEP
		print(f"  Using {step}")

	# Just to check we can infer every net's run, test:

	for net in range(lowest, highest + 1, step):
		if infer_run(net) == None:
			print(f"Could not infer the run for net {net}, edit infer_run() function to fix.")
			sys.exit()

	fen = input("FEN? (leave blank for default)  ")
	if fen.strip() == "":
		fen = DEFAULT_FEN
		print(f"  Using {fen}")

	move = input("Move? (UCI format, leave blank for default)  ")
	if move.strip() == "":
		move = DEFAULT_MOVE
		print(f"  Using {move}")

	return lowest, highest, step, fen, move


def graph(nets, policies, values, title):

	fig, ax = plt.subplots()
	ax.plot(nets, policies, color = "red", marker = "o")
	ax.set_xlabel("year", fontsize = 14)
	ax.set_ylabel("policy", color = "red", fontsize = 14)

	ax2 = ax.twinx()
	ax2.plot(nets, values, color = "blue", marker = "o")
	ax2.set_ylabel("value", color = "blue", fontsize = 14)

	plt.title(title)
	plt.show()


def main():

	try:
		os.mkdir(NETWORKS)
	except FileExistsError:
		pass

	print()

	lowest, highest, step, fen, move = interrogate_user()

	nets = []
	policies = []
	values = []

	print()

	engine = Engine(ENGINE)

	for net in range(lowest, highest + 1, step):
		try:
			policy, value = engine.test(fen, move, net)
			nets.append(net)
			policies.append(policy)
			values.append(value * 100)
		except NetNotKnown:
			print(f"(net {net} not known)")

	engine.quit()
	graph(nets, policies, values, f"P({move}) and V for:  {fen}")


if __name__ == "__main__":
	main()
