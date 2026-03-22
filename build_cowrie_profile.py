#!/usr/bin/env python3
"""Cowrie OS profile builder and filesystem capture.

Run this on a target host to create Cowrie virtual filesystem artifacts
matching the host environment, plus a cowrie.cfg with arch/os details.

Usage:
  python build_cowrie_profile.py --outdir /tmp/cowrie-profile --hostfs / --profile ubuntu-24.04
"""

import argparse
import configparser
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_cmd(cmd, timeout=30, check=False, capture_output=True):
    if capture_output:
        completed = subprocess.run(cmd, shell=True, timeout=timeout,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)
    else:
        completed = subprocess.run(cmd, shell=True, timeout=timeout)
    if check and completed.returncode != 0:
        raise RuntimeError("command failed: %s\n%s" % (cmd, completed.stdout if capture_output else ""))
    return completed.returncode, (completed.stdout.strip() if capture_output else "")


def is_command_available(cmd):
    return shutil.which(cmd) is not None


def ensure_pip(python_bin):
    rc, out = run_cmd(f"{python_bin} -m pip --version", timeout=30, check=False)
    if rc == 0:
        return

    print(f"    pip is not installed for {python_bin}. attempting to bootstrap via ensurepip")
    rc2, out2 = run_cmd(f"{python_bin} -m ensurepip --upgrade", timeout=120, check=False)
    if rc2 != 0:
        raise RuntimeError(
            f"Could not install pip inside virtualenv.\n"
            f"Run manually: {python_bin} -m ensurepip --upgrade\n"
            "Then: {python_bin} -m pip install --upgrade pip\n"
            "Or install system package python3-pip and rerun."
        )

    rc3, out3 = run_cmd(f"{python_bin} -m pip --version", timeout=30, check=False)
    if rc3 != 0:
        raise RuntimeError(
            f"pip bootstrapped but still unavailable for {python_bin}.\n"
            "Please install python3-pip and rerun."
        )


def install_cowrie():
    print("[+] Ensuring Cowrie is installed via git clone (recommended)")
    # prefer existing `cowrie` command if already installed
    if is_command_available("cowrie"):
        print("    cowrie command exists")
        return "cowrie"

    if not is_command_available("git"):
        raise RuntimeError("git is required to install Cowrie from source")

    install_dir = Path.home() / ".cowrie-src"
    if install_dir.exists():
        print(f"    existing cowrie clone found at {install_dir}")
    else:
        print(f"    cloning Cowrie to {install_dir}")
        run_cmd(f"git clone https://github.com/cowrie/cowrie.git {install_dir}", timeout=600, check=True)

    # setup virtualenv and install requirements
    venv_dir = install_dir / "venv"
    if not venv_dir.exists():
        print("    creating virtualenv for Cowrie")
        run_cmd(f"python3 -m venv {venv_dir}", timeout=300, check=True)

    # Activate works via explicit path commands below.
    python_bin = venv_dir / "Scripts" / "python.exe" if os.name == "nt" else venv_dir / "bin" / "python3"

    ensure_pip(python_bin)

    print("    installing Cowrie requirements in virtualenv")
    run_cmd(f"{python_bin} -m pip install --upgrade pip", timeout=300, check=True)
    run_cmd(f"{python_bin} -m pip install -r {install_dir / 'requirements.txt'}", timeout=600, check=True)

    # install cowrie in development mode
    run_cmd(f"cd {install_dir} && {python_bin} -m pip install -e .", timeout=600, check=True)

    # verify createfs executable exists and works
    createfs_bin = venv_dir / "bin" / "createfs" if os.name != "nt" else venv_dir / "Scripts" / "createfs.exe"
    if not createfs_bin.exists():
        raise RuntimeError(f"createfs executable not found at {createfs_bin}")
    
    try:
        rc, out = run_cmd(f"{createfs_bin} --help", timeout=30, check=False)
        print(f"    cowrie createfs available at {createfs_bin}: OK")
    except Exception as exc:
        raise RuntimeError(f"Cowrie createfs command not functional: {exc}")

    return str(createfs_bin)



def collect_host_info():
    info = {
        "profile_timestamp": datetime.utcnow().isoformat() + "Z",
        "uname": platform.uname()._asdict(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }

    def read_if_exists(path):
        p = Path(path)
        if p.exists():
            try:
                return p.read_text(errors="ignore").strip()
            except Exception:
                return "<read error>"
        return None

    for path in ["/etc/os-release", "/etc/lsb-release", "/etc/redhat-release", "/etc/debian_version"]:
        txt = read_if_exists(path)
        if txt:
            info[Path(path).name] = txt
    return info


def produce_cowrie_cfg(outcfg, profile_name, host_info):
    cfg = configparser.ConfigParser()
    cfg["profile"] = {
        "name": profile_name,
        "created": host_info["profile_timestamp"],
        "machine": host_info["machine"],
        "processor": host_info["processor"],
        "os": host_info["system"],
        "release": host_info["release"],
    }
    cfg["system"] = {
        # don't output this - buildit from the shell variables below so the hostname is correct in cowrie
        #"uname": " ".join([host_info["uname"][k] for k in ["system", "node", "release", "version", "machine"] if host_info["uname"].get(k)]),
        "cpu_count": str(host_info.get("cpu_count", "")),
        "python_version": host_info.get("python_version", ""),
    }

    # Populate shell section with architecture details.
    # cowrie expects keys like kernel_version, kernel_build_string, kernel_machine, kernel_os.
    cfg["shell"] = {
        "kernel_version": host_info["uname"].get("release", ""),
        "kernel_build_string": host_info["uname"].get("version", ""),
        "kernel_machine": host_info["uname"].get("machine", ""),
        "kernel_os": host_info["uname"].get("system", ""),
    }

    sshd_version = ""
    try:
        _, sshd_version = run_cmd("sshd -V", timeout=10, check=False)
    except Exception:
        sshd_version = "<not available>"
    cfg["ssh"] = {
        "sshd_version": sshd_version.replace("\n", " "),
        "ssh_client_version": (run_cmd("ssh -V", timeout=10)[1] or "<not available>").replace("\n", " "),
    }

    with open(outcfg, "w", encoding="utf-8") as f:
        cfg.write(f)
    print(f"[+] Cowrie config written: {outcfg}")


def generate_cowrie_filesystem(createfs_bin, outdir, hostfs, profile_name):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    # createfs_bin is the path to the createfs executable
    # createfs -l <local_root_dir> -o <output_file>

    output_file = Path(outdir) / "files.pickle"
    args_list = [
        f"{createfs_bin} -l {hostfs} -o {output_file}",
        f"{createfs_bin} -v -l {hostfs} -o {output_file}",
    ]

    last_err = None
    for args in args_list:
        try:
            print(f"[+] Running {args}")
            rc, out = run_cmd(args, timeout=1800, check=False)
            print(out)
            if rc == 0:
                print("[+] createfs succeeded")
                return
            last_err = (rc, out)
        except Exception as e:
            last_err = (None, str(e))
            print("    createfs attempt failed:", e)

    raise RuntimeError("Cowrie createfs failed: %s" % (last_err,))


def main():
    parser = argparse.ArgumentParser(description="Build Cowrie-compatible OS profile + FS artifacts")
    parser.add_argument("--outdir", required=True, help="Output directory for cowrie artifacts")
    parser.add_argument("--hostfs", default="/", help="Host filesystem root to capture")
    parser.add_argument("--profile", default="host-profile", help="Name for cowrie profile")
    parser.add_argument("--cfg", default="cowrie.cfg", help="cowrie.cfg output filename")
    parser.add_argument("--no-install", action="store_true", help="Do not attempt to install Cowrie automatically")
    args = parser.parse_args()

    outdir = Path(args.outdir).absolute()
    outcfg = outdir / args.cfg
    outdir.mkdir(parents=True, exist_ok=True)

    if args.no_install:
        # when --no-install is specified, look for createfs executable in PATH
        if is_command_available("createfs"):
            createfs_bin = "createfs"
        else:
            raise RuntimeError("createfs executable not found in PATH. Install Cowrie and rerun.")
    else:
        createfs_bin = install_cowrie()

    host_info = collect_host_info()
    metadata_file = outdir / "host_profile.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(host_info, f, indent=2)
    print(f"[+] Host info stored at {metadata_file}")

    produce_cowrie_cfg(outcfg, args.profile, host_info)

    generate_cowrie_filesystem(createfs_bin, str(outdir / "fs"), args.hostfs, args.profile)

    print("\n[✅] Cowrie profile package created successfully")
    print(f"- fs: {outdir / 'fs'}")
    print(f"- cfg: {outcfg}")
    print(f"- metadata: {metadata_file}")


if __name__ == "__main__":
    main()
