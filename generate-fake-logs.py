#!/usr/bin/env python3
"""
Fake log generator for various operating systems using faker library.

Generates realistic-looking log entries for core /var/log files to simulate
a live operating system. Supports Ubuntu, RHEL, Alpine, Amazon Linux, and Debian.
"""

import argparse
from pathlib import Path
from faker import Faker
import random
from datetime import datetime, timedelta


# Initialize faker
fake = Faker()


def generate_syslog_entry(timestamp, hostname):
    """Generate a fake syslog entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    process = random.choice(["systemd", "sshd", "cron", "kernel", "apt", "yum", "apache2", "nginx"])
    pid = random.randint(1000, 9999)
    message = random.choice([
        f"Started {fake.word()}.",
        f"Stopped {fake.word()}.",
        f"Reloaded {fake.word()}.",
        f"Failed to start {fake.word()}.",
        f"Connection from {fake.ipv4()} port {random.randint(1024, 65535)}",
        f"Reading package lists...",
        f"Updated: {fake.word()}",
    ])
    return f"{ts} {hostname} {process}[{pid}]: {message}"


def generate_auth_entry(timestamp, hostname):
    """Generate a fake auth log entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    user = fake.user_name()
    ip = fake.ipv4()
    port = random.randint(1024, 65535)
    method = random.choice(["password", "publickey"])
    outcome = random.choice(["Accepted", "Failed", "Invalid user"])
    return f"{ts} {hostname} sshd[{random.randint(1000, 9999)}]: {outcome} {method} for {user} from {ip} port {port} ssh2"


def generate_kern_entry(timestamp, hostname):
    """Generate a fake kernel log entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    level = random.choice(["INFO", "WARNING", "ERROR"])
    message = random.choice([
        f"usb 1-1: new high-speed USB device number {random.randint(1, 10)} using ehci-pci",
        f"EXT4-fs ({fake.word()}): mounted filesystem with ordered data mode",
        f"IPv6: ADDRCONF(NETDEV_UP): {fake.word()}: link is not ready",
        f"CPU{random.randint(0, 7)}: Core temperature above threshold",
        f"Memory cgroup out of memory: Kill process {random.randint(1000, 9999)}",
    ])
    return f"{ts} {hostname} kernel: [{random.uniform(0, 10):.6f}] {message}"


def generate_mail_entry(timestamp, hostname):
    """Generate a fake mail log entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    program = random.choice(["postfix", "sendmail", "dovecot", "saslauthd"])
    pid = random.randint(1000, 9999)
    actions = [
        f"connect from {fake.ipv4()}",
        f"disconnect from {fake.ipv4()}",
        f"NOQUEUE: reject: RCPT from {fake.ipv4()}: 550 5.1.1 <{fake.email()}>: Recipient address rejected",
        f"to=<{fake.email()}>, relay=local, delay=0.01, delays=0.00/0.00/0.00/0.01, dsn=2.0.0, status=sent",
        f"from=<{fake.email()}>, size={random.randint(1000, 50000)}, nrcpt=1 (queue active)",
        f"removed",
        f"stat=Sent",
        f"authentication failed: no mechanism available",
        f"warning: hostname {fake.domain_name()} does not resolve to address",
    ]
    message = random.choice(actions)
    return f"{ts} {hostname} {program}[{pid}]: {message}"


def generate_cron_entry(timestamp, hostname):
    """Generate a fake cron log entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    user = random.choice(["root", "www-data", "apache", fake.user_name()])
    pid = random.randint(1000, 9999)
    commands = [
        f"({user}) CMD ({random.choice(['/usr/bin/php', '/usr/bin/python3', '/bin/bash', '/usr/sbin/logrotate'])} {fake.word()})",
        f"({user}) RELOAD ({random.choice(['/etc/cron.daily', '/etc/cron.hourly', '/etc/cron.weekly'])})",
        f"({user}) LIST ({user})",
        f"({user}) END ({user})",
        f"({user}) START ({user})",
        f"({user}) INFO (Skipping @reboot jobs -- not system startup)",
    ]
    message = random.choice(commands)
    return f"{ts} {hostname} CRON[{pid}]: {message}"


def generate_daemon_entry(timestamp, hostname):
    """Generate a fake daemon log entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    daemon = random.choice(["apache2", "nginx", "mysql", "postgresql", "sshd", "cups", "bluetoothd"])
    pid = random.randint(1000, 9999)
    messages = [
        f"Starting {daemon} daemon",
        f"Stopping {daemon} daemon",
        f"Reloading {daemon} configuration",
        f"{daemon} is running",
        f"Connection from {fake.ipv4()}:{random.randint(1024, 65535)}",
        f"Worker process {pid} exited",
        f"Server ready to accept connections",
        f"Configuration reloaded",
        f"Failed to start {daemon}: permission denied",
        f"{daemon} listening on port {random.randint(80, 9999)}",
    ]
    message = random.choice(messages)
    return f"{ts} {hostname} {daemon}[{pid}]: {message}"


def generate_boot_entry(timestamp, hostname):
    """Generate a fake boot log entry at given timestamp."""
    ts = timestamp.strftime("%b %d %H:%M:%S")
    messages = [
        f"Starting kernel ...",
        f"Loading Linux {random.randint(4, 6)}.{random.randint(0, 20)}.{random.randint(0, 50)}-generic",
        f"Mounted /sys/kernel/security",
        f"Started Load Kernel Modules",
        f"Reached target Basic System",
        f"Started Network Manager",
        f"Started SSH Daemon",
        f"Started Apache Web Server",
        f"System boot complete",
        f"Welcome to {hostname}!",
    ]
    message = random.choice(messages)
    return f"{ts} {hostname} systemd[1]: {message}"


def generate_package_entry(timestamp, hostname, package_manager="apt"):
    """Generate a fake package manager log entry at given timestamp."""
    ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    if package_manager == "apt":
        actions = [
            f"Started {random.choice(['Unpacking', 'Setting up', 'Processing triggers for'])} {fake.word()}",
            f"Installed {fake.word()} ({fake.numerify('1.##.#-1')})",
            f"Upgraded {fake.word()} ({fake.numerify('1.##.#-1')} to {fake.numerify('1.##.#-2')})",
            f"Removed {fake.word()} ({fake.numerify('1.##.#-1')})",
            f"Reading package lists...",
            f"Building dependency tree",
            f"Reading state information...",
        ]
        message = random.choice(actions)
        return f"{ts} {message}"
    elif package_manager == "yum":
        actions = [
            f"Installed: {fake.word()}-{fake.numerify('1.##.#-1')}.x86_64",
            f"Updated: {fake.word()}-{fake.numerify('1.##.#-1')}.x86_64",
            f"Erased: {fake.word()}-{fake.numerify('1.##.#-1')}.x86_64",
            f"Resolving Dependencies",
            f"Running transaction check",
            f"Verifying : {fake.word()}-{fake.numerify('1.##.#-1')}.x86_64",
        ]
        message = random.choice(actions)
        return f"{ts} {message}"
    elif package_manager == "dpkg":
        actions = [
            f"unpack {fake.word()} {fake.numerify('1.##.#-1')}",
            f"install {fake.word} <none> {fake.numerify('1.##.#-1')}",
            f"upgrade {fake.word} {fake.numerify('1.##.#-1')} {fake.numerify('1.##.#-2')}",
            f"remove {fake.word} {fake.numerify('1.##.#-1')} {fake.numerify('1.##.#-1')}",
            f"purge {fake.word} {fake.numerify('1.##.#-1')}",
        ]
        message = random.choice(actions)
        return f"{ts} {message}"


# Map OS types to log types
OS_LOG_MAPPING = {
    "ubuntu": {
        "syslog": "syslog",
        "auth.log": "auth",
        "kern.log": "kern",
        "boot.log": "boot",
        "cron.log": "cron",
        "daemon.log": "daemon",
        "mail.log": "mail",
        "user.log": "auth",
        "apt/history.log": "apt",
        "dpkg.log": "dpkg",
    },
    "rhel": {
        "messages": "syslog",
        "secure": "auth",
        "dmesg": "kern",
        "boot.log": "boot",
        "cron": "cron",
        "maillog": "mail",
        "yum.log": "yum",
    },
    "alpine": {
        "messages": "syslog",
        "auth.log": "auth",
        "kern.log": "kern",
        "boot.log": "boot",
        "cron.log": "cron",
        "mail.log": "mail",
    },
    "amazon": {
        "messages": "syslog",
        "secure": "auth",
        "dmesg": "kern",
        "boot.log": "boot",
        "cron": "cron",
        "maillog": "mail",
        "yum.log": "yum",
    },
    "debian": {
        "syslog": "syslog",
        "auth.log": "auth",
        "kern.log": "kern",
        "boot.log": "boot",
        "cron.log": "cron",
        "daemon.log": "daemon",
        "mail.log": "mail",
        "user.log": "auth",
        "apt/history.log": "apt",
        "dpkg.log": "dpkg",
    },
}


def generate_fake_logs(os_type, output_dir, hostname=None):
    """Generate fake log entries for the specified OS using faker."""
    if os_type not in OS_LOG_MAPPING:
        raise ValueError(f"Unsupported OS: {os_type}. Supported: {list(OS_LOG_MAPPING.keys())}")

    # Default hostname to a generic name if not provided
    if hostname is None:
        hostname = f"{os_type}-host"

    log_dir = Path(output_dir) / "var" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    for log_file, log_type in OS_LOG_MAPPING[os_type].items():
        log_path = log_dir / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist
        num_entries_for_file = random.randint(100, 1000)

        # Generate a sequence of monotonically increasing timestamps for this file
        current_timestamp = datetime.now() - timedelta(hours=24)

        with open(log_path, "w") as f:
            for _ in range(num_entries_for_file):
                current_timestamp += timedelta(seconds=random.randint(10, 300))
                if log_type == "syslog":
                    entry = generate_syslog_entry(current_timestamp, hostname)
                elif log_type == "auth":
                    entry = generate_auth_entry(current_timestamp, hostname)
                elif log_type == "kern":
                    entry = generate_kern_entry(current_timestamp, hostname)
                elif log_type == "mail":
                    entry = generate_mail_entry(current_timestamp, hostname)
                elif log_type == "cron":
                    entry = generate_cron_entry(current_timestamp, hostname)
                elif log_type == "daemon":
                    entry = generate_daemon_entry(current_timestamp, hostname)
                elif log_type == "boot":
                    entry = generate_boot_entry(current_timestamp, hostname)
                elif log_type == "apt":
                    entry = generate_package_entry(current_timestamp, hostname, "apt")
                elif log_type == "yum":
                    entry = generate_package_entry(current_timestamp, hostname, "yum")
                elif log_type == "dpkg":
                    entry = generate_package_entry(current_timestamp, hostname, "dpkg")
                else:
                    entry = generate_syslog_entry(current_timestamp, hostname)  # fallback
                f.write(entry + "\n")

        print(f"Generated {num_entries_for_file} entries in {log_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate fake log files for various operating systems using logfaker.")
    parser.add_argument("--os", required=True, choices=["ubuntu", "rhel", "alpine", "amazon", "debian"],
                        help="Operating system type")
    parser.add_argument("--output-dir", required=True, help="Output directory for log files")
    parser.add_argument("--hostname", default=None, help="Hostname to use in log entries (default: {os}-host)")
    args = parser.parse_args()

    generate_fake_logs(args.os, args.output_dir, hostname=args.hostname)
    hostname_display = args.hostname or f"{args.os}-host"
    print(f"Fake logs for {args.os} generated in {args.output_dir} with hostname: {hostname_display}")



if __name__ == "__main__":
    main()

