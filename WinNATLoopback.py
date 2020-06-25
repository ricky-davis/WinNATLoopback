import argparse
import atexit
import ctypes
import os
import signal
import subprocess
import sys
import time

import psutil
import requests


def get_public_ip():
    url = "https://api.ipify.org?format=json"
    x = (requests.get(url)).json()
    return x["ip"]


publicIP = get_public_ip()


class WinNATLoopback:
    version = "v1.0.0"

    def __init__(self):
        print(f"WinNATLoopback {WinNATLoopback.version}")
        self.isExecutable = os.path.samefile(sys.executable, sys.argv[0])
        self.DaemonProcess = Daemon.launch(executable=self.isExecutable)
        atexit.register(WinNATLoopback.teardown_interface)
        WinNATLoopback.setup_interface()
        while True:
            time.sleep(1)

    @staticmethod
    def setup_interface():
        addrs = psutil.net_if_addrs()
        LBName = [x for x in addrs.keys() if "loopback" in x.lower()]
        if len(LBName) > 0 and len(LBName) < 2:
            LBName = LBName[0]
            LBInt = addrs[LBName]
            if not [x for x in LBInt if x.address == publicIP]:
                cmd = f"netsh int ip add addr \"{LBName}\" {publicIP}/32 st=ac"
                print(cmd)
                subprocess.call(cmd, shell=False)
                print(f"Added Loopback for {publicIP}")
                print("Press CTRL+C to stop and delete the loopback.")
            else:
                print(f"Loopback already exists for {publicIP}")

    @ staticmethod
    def teardown_interface():
        addrs = psutil.net_if_addrs()
        LBName = [x for x in addrs.keys() if "loopback" in x.lower()]
        if len(LBName) > 0 and len(LBName) < 2:
            LBName = LBName[0]
            LBInt = addrs[LBName]
            if [x for x in LBInt if x.address == publicIP]:
                cmd = f"netsh int ip delete addr \"{LBName}\" {publicIP}"
                print(cmd)
                subprocess.call(cmd, shell=False)
                print(f"Deleted Loopback for {publicIP}")


class Daemon:
    """
        Daemon process
    """

    @ staticmethod
    def launch(executable):
        if executable:
            daemonCMD = [sys.executable, "--daemon", "-c", str(os.getpid()), ]
        else:
            daemonCMD = [sys.executable, sys.argv[0],
                         "--daemon", "-c", str(os.getpid()), ]
        return subprocess.Popen(
            daemonCMD,
            shell=False,
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP,
        )

    @ staticmethod
    def daemon(consolePID):
        while psutil.pid_exists(int(consolePID)):
            time.sleep(0.5)
        try:
            WinNATLoopback.teardown_interface()
            for child in psutil.Process(int(consolePID)).children():
                os.kill(child.pid, signal.CTRL_C_EVENT)
        except KeyboardInterrupt as e:
            print(e)


if __name__ == "__main__":
    try:
        os.system(f"title WinNATLoopback {WinNATLoopback.version}")
    except:
        pass
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            print("Please relaunch me as Administrator!")
            input()
        else:
            parser = argparse.ArgumentParser()
            parser.add_argument("-d", "--daemon", dest="daemon",
                                action="store_true")
            parser.add_argument(
                "-c",
                "--consolepid",
                help="Set the consolePID for the Daemon",
                type=str.lower,
            )
            args = parser.parse_args()
            if args.daemon:
                if args.consolepid:
                    kernel32 = ctypes.WinDLL("kernel32")
                    user32 = ctypes.WinDLL("user32")
                    SW_HIDE = 0
                    hWnd = kernel32.GetConsoleWindow()
                    if hWnd:
                        user32.ShowWindow(hWnd, SW_HIDE)

                    Daemon().daemon(args.consolepid)
                else:
                    print("Insufficient launch options!")
            else:
                WinNATLoopback()
    except KeyboardInterrupt:
        pass
