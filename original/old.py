# Originally by an anonymous Discorder

import subprocess
from matplotlib import pyplot as plt
import os
import requests

BAD_FEN = "Q7/Q7/8/6pk/5n2/8/1q6/7K w - - 0 1"
UCI_POLICY_MOVE = "a8f3"

def dl_net(net_number):
    t = requests.get("https://training.lczero.org/networks/1").text
    nets = t.split('<td><a href="/get_network?sha=')
    nets = [n.split('">')[0].replace("\n", "") for n in nets]
    net = [n for n in nets if f"run1_{net_number}.pb" in n][0]
    print(f"downloading {net_number}")
    open(f"lc0/weights_run1_{net_number}.pb.gz", "wb").write(requests.get("https://training.lczero.org/get_network?sha=" + net.split('"')[0]).content)

def test_position(fen, net):
    if not os.path.exists(f"lc0/weights_run1_{net}.pb.gz"):
        dl_net(net)

    p = subprocess.Popen(["lc0/lc0.exe"], stdin = subprocess.PIPE, stdout = subprocess.PIPE)

    p.stdin.write("uci\n".encode("utf8"))
    p.stdin.flush()
    while "uciok" not in (l := p.stdout.readline().decode("utf8")):
        #print(f"({l.strip()})")
        pass

    #print(f"({l.strip()})")
    p.stdin.write(f"setoption name WeightsFile value lc0/weights_run1_{net}.pb.gz\n".encode("utf8"))
    p.stdin.flush()

    p.stdin.write("setoption name Backend value cudnn\n".encode("utf8"))
    p.stdin.flush()

    p.stdin.write("setoption name VerboseMoveStats value true\n".encode("utf8"))
    p.stdin.flush()

    p.stdin.write("setoption name LogLiveStats value true\n".encode("utf8"))
    p.stdin.flush()

    p.stdin.write(f"position fen {fen}\n".encode("utf8"))
    p.stdin.flush()

    p.stdin.write("isready\n".encode("utf8"))
    p.stdin.flush()

    while "readyok" not in (l := p.stdout.readline().decode("utf8")):
        #print(f"({l.strip()})")
        pass

    #print(f"({l.strip()})")
    p.stdin.write("go nodes 1\n".encode("utf8"))
    p.stdin.flush()

    cp = None
    while True:
        l = p.stdout.readline().decode("utf8")
        if "info string " + UCI_POLICY_MOVE in l:
            cp = float(l.split("P: ", 1)[1].split("%")[0].strip())
            break

    p.terminate()
    return cp, l.strip()

nets_to_test  = [65000 + x * 100 for x in range(1000) if 65000 + x * 100 < 67820]
x = []
y = []
for net in nets_to_test:
    x.append(net)
    try:
        y.append(int(open(f"cache/{net}").read().strip().split(";")[0]))
    except:
        r, l = test_position(BAD_FEN, net)
        open(f"cache/{net}", "w").write(str(r) + ";" + l)
        y.append(r)

plt.plot(x, y)
plt.title(f"Policy score for {BAD_FEN} with T60 nets")
plt.show()
