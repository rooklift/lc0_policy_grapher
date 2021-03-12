# Originally by an anonymous Discorder

ENGINE = "C:\\Programs (self-installed)\\lc0-cuda\\lc0.exe"
NETWORKS = "C:\\Users\\Owner\\Documents\\Misc\\Chess\\Lc0 Networks"

import os, subprocess, sys
import requests
from matplotlib import pyplot as plt

lczero_nets = [None, dict(), dict(), dict()]		# for runs 1, 2, 3


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
		ret = self.process.stdout.readline().decode("utf8").strip()
		# print(ret)
		return ret

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

	def test(self, fen, move, net, nodes, desired_stats):

		self.setoption("WeightsFile", os.path.join(NETWORKS, f"{net}.pb.gz"))
		self.send("ucinewgame")
		self.send(f"position fen {fen}")
		self.send("isready")
		while "readyok" not in self.readline():
			pass
		self.send(f"go nodes {nodes}")

		stats = dict()

		for stat in desired_stats:
			stats[stat] = None

		while True:
			line = self.readline()
			if f"info string {move}" in line:
				for stat in desired_stats:
					raw = line.split(f"({stat}:")[1].split(")")[0]
					if raw[-1] == "%":
						raw = raw[:-1]
					stats[stat] = float(raw)
				print(stats)
			if "bestmove" in line:
				break

		return stats


def infer_run(net):

	if net >=  60000 and net <  70000:
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


def get_sha(net):

	global lczero_nets

	run = infer_run(net)
	if run == None:
		return None

	if len(lczero_nets[run]) == 0:
		dl_inventory(run)

	try:
		return lczero_nets[run][net]
	except:
		return None


def dl_net(net, sha):

	with open(os.path.join(NETWORKS, f"{net}.pb.gz"), "wb") as outfile:
		outfile.write(requests.get(f"https://training.lczero.org/get_network?sha={sha}").content)


def parse_flags():

	flags = ["fen", "modulo", "start_net_id", "move", "nodes"]
	stats = ["D", "P", "Q", "V"]

	flags_ret = dict()
	stats_ret = dict()

	for flag in flags:
		for i, arg in enumerate(sys.argv):
			if arg == flag or arg == "-" + flag or arg == "--" + flag:
				try:
					val = sys.argv[i + 1]
					flags_ret[flag] = val
				except IndexError:
					pass

	for stat in stats:
		for arg in sys.argv:
			if arg.upper() == stat or arg.upper() == "-" + stat or arg.upper() == "--" + stat:
				stats_ret[stat] = True

	return flags_ret, stats_ret


def graph(nets, stats, fen, move):

	fig, ax = plt.subplots()

	desired_stats = sorted(list(stats[0]))		# Gets keys

	values = [foo[desired_stats[0]] for foo in stats]

	ax.plot(nets, values, color = "red", marker = "o")
	ax.set_xlabel("network", fontsize = 14)
	ax.set_ylabel(f"{desired_stats[0]} ({move})", color = "red", fontsize = 14)

	if len(desired_stats) > 1:
		values = [foo[desired_stats[1]] for foo in stats]
		ax2 = ax.twinx()
		ax2.plot(nets, values, color = "blue", marker = "o")
		ax2.set_ylabel(f"{desired_stats[1]} ({move})", color = "blue", fontsize = 14)

	plt.title(fen)
	plt.show()


def main():

	try:
		os.mkdir(NETWORKS)
	except FileExistsError:
		pass

	flag_dict, stats_dict = parse_flags()

	desired_stats = list(stats_dict)		# Gets keys

	if len(desired_stats) < 1 or len(desired_stats) > 2:
		print("Must specify 1 or 2 stats to track: -D -P -Q -V")
		sys.exit()

	try:
		net = int(flag_dict["start_net_id"])
		modulo = int(flag_dict["modulo"])
		nodes = int(flag_dict["nodes"])
		move = flag_dict["move"]
		fen = flag_dict["fen"]
	except KeyError:
		print("Required args: start_net_id , modulo , move , nodes, fen")
		sys.exit()

	print()

	nets = []
	stats = []		# Each item being a dict of stat --> value

	engine = Engine(ENGINE)

	while 1:

		print(net, end=" ", flush=True)

		if not os.path.exists(os.path.join(NETWORKS, f"{net}.pb.gz")):
			sha = get_sha(net)
			if sha:
				print(f"(downloading {sha[:8]})", end=" ", flush=True)
				dl_net(net, sha)
			else:
				print(f"(net {net} not known, ending run)")
				break

		new_stats = engine.test(fen, move, net, nodes, desired_stats)

		nets.append(net)
		stats.append(new_stats)

		net += modulo

	engine.quit()
	graph(nets, stats, fen, move)


if __name__ == "__main__":
	main()
