# Cowrie OS Profiler

A toolkit for creating customized Cowrie honeypot profiles from golden images. Capture your organization's unique OS configuration, filesystem structure, and generate system activity patterns to deploy highly realistic honeypot instances.

## Overview

Cowrie is a popular SSH honeypot used for threat research and detection testing. However, default Cowrie deployments often lack authentic OS characteristics. This project provides tools to:

1. **Capture** real OS filesystems and configurations from a golden image
2. **Generate** realistic system activity logs that simulate a live operating system
3. **Package** everything into reusable Cowrie profiles deployable across your infrastructure

Organizations can either:
- Use pre-built profiles directly from the repository
- Generate custom profiles matching their specific OS configuration and log patterns
- Share standardized profiles across their security team

## Features

- **Filesystem Capture**: Extract complete directory structures using Cowrie's native `createfs` tool
- **OS Metadata Collection**: Automatically detect and record OS version, architecture, kernel details, and SSH configuration
- **Realistic Log Generation**: Create authentic-looking `/var/log` entries across multiple Linux distributions
- **Multi-OS Support**: Ubuntu, RHEL, Alpine Linux, Amazon Linux, and Debian
- **Consistent Configuration**: Apply custom hostnames and system identities across all generated artifacts
- **Zero Dependencies (Optional)**: Automatic Cowrie installation via GitHub clone and virtualenv

## Project Structure

```
cowrie-os-profiler/
├── build_cowrie_profile.py      # Capture filesystem & OS config from golden image
├── generate-fake-logs.py        # Generate realistic log entries
├── profiles/                    # Pre-built customized profiles (ready to deploy)
│   ├── ubuntu-22.04/
│   ├── rhel-8/
│   └── ...
├── README.md                    # This file
└── requirements.txt             # Python dependencies (faker, etc.)
```

## Installation

### Prerequisites

- Python 3.8+
- Git (for Cowrie installation)
- Golden image OS (for capturing filesystem)
- pip (auto-bootstrapped in virtualenv if needed)

### Setup

```bash
# Clone this repository
git clone <repo-url>
cd cowrie-os-profiler

# Install Python dependencies
pip install faker
```

## Usage

### Step 1: Build OS Profile from Golden Image

Capture your organization's golden OS image (filesystem + configuration):

```bash
python3 build_cowrie_profile.py \
  --outdir ./my-profile \
  --profile my-custom-os \
  --hostfs /
```

**Arguments:**
- `--outdir`: Output directory for generated artifacts (required)
- `--hostfs`: Path to filesystem root to capture (default: `/`)
- `--profile`: Profile name (default: `host-profile`)
- `--cfg`: Custom cowrie.cfg path (optional; uses default if not specified)
- `--no-install`: Skip Cowrie installation/verification (assumes `createfs` is available)

**Output Files:**
- `fs/files.pickle`: Pickled filesystem structure (used by Cowrie)
- `cowrie.cfg`: Cowrie configuration with OS metadata and shell section
- `host_profile.json`: JSON metadata (hostname, kernel version, CPU count, etc.)

**Example:**
```bash
python3 build_cowrie_profile.py --outdir ./profiles/ubuntu-jammy --profile ubuntu-jammy
```

### Step 2: Generate Realistic Log Files

Create synthetic system activity logs for your profile:

```bash
python3 generate-fake-logs.py \
  --os ubuntu \
  --output-dir ./my-profile \
  --hostname myorg-honeypot-01
```

**Arguments:**
- `--os`: Operating system type (required)
  - Options: `ubuntu`, `rhel`, `alpine`, `amazon`, `debian`
- `--output-dir`: Output directory for logs (required)
- `--hostname`: Custom hostname for log entries (default: `{os}-host`)

**Features:**
- Generates 100-1000 realistic entries per log file (randomized)
- Log files include: system logs, authentication logs, kernel logs, cron logs, boot logs, mail server logs, daemon logs, package manager logs
- Consistent hostname across all entries
- Monotonic timestamps within each file (independent across files)
- Realistic content for each log type: SSH auth attempts, mail server activity, cron jobs, service messages, package operations, kernel events

**Output Structure:**
```
my-profile/
└── var/
    └── log/
        ├── syslog
        ├── auth.log
        ├── kern.log
        ├── cron
        ├── boot.log
        ├── apt/history.log    (Debian/Ubuntu)
        ├── yum.log            (RHEL/Amazon)
        └── ...
```

### Complete Workflow

```bash
# 1. Build profile from golden image
python3 build_cowrie_profile.py \
  --outdir ./my-profile \
  --profile my-org-ubuntu-22.04

# 2. Generate realistic logs
python3 generate-fake-logs.py \
  --os ubuntu \
  --output-dir ./my-profile \
  --hostname my-org-honeypot

# 3. Deploy to Cowrie
# Copy my-profile/ contents into Cowrie's data directory
```

## Supported Operating Systems

### Ubuntu / Debian
- Log files: syslog, auth.log, kern.log, boot.log, cron, daemon, mail, user, apt/history.log, dpkg.log
- Generated entries: systemd messages, SSH auth, kernel events, package manager activity

### RHEL / Amazon Linux
- Log files: messages, secure, dmesg, boot.log, cron, maillog, yum.log
- Generated entries: systemd messages, SSH auth, kernel events, package manager activity

### Alpine Linux
- Log files: messages, auth.log, kern.log, boot.log, cron, mail
- Generated entries: systemd messages, SSH auth, kernel events

## Generated Artifacts

### Filesystem (files.pickle)
- Binary pickle format used by Cowrie
- Contains complete directory tree + file metadata
- Deployed to Cowrie's `data/fs/` directory

### Configuration (cowrie.cfg)
Includes sections:
- `[profile]`: Creation timestamp, machine info, processor details
- `[system]`: uname output, CPU count, Python version
- `[shell]`: Kernel version, build string, architecture, OS info
- `[ssh]`: SSH server and client versions (detected from host)

### Log Files (var/log/)
- Realistic entries with proper timestamps
- Consistent hostname across all files
- Varied event types (auth, system, kernel, package management)
- Ready to deploy to Cowrie's emulated filesystem

## Advanced Usage

### Custom Hostnames
Apply organization-specific hostnames to all log entries:
```bash
python3 generate-fake-logs.py \
  --os rhel \
  --output-dir ./my-profile \
  --hostname "security-test-honeypot-001"
```

### No-Install Mode
If Cowrie is already installed elsewhere:
```bash
python3 build_cowrie_profile.py \
  --outdir ./my-profile \
  --no-install
```
(Assumes `createfs` is in your PATH)

### Capturing Non-Root Filesystems
Capture specific directories as the emulated root:
```bash
python3 build_cowrie_profile.py \
  --outdir ./my-profile \
  --hostfs /opt/my-golden-image
```

## File Format Details

### Timestamp Generation (Logs)
- All timestamps span 24 hours into the past through now
- Each log file has independent timestamp progression
- Within a file: timestamps strictly monotonic, incrementing 10-300 seconds per entry
- Across files: different event timelines (realistic behavior)

### Log Entry Formats
- **Syslog**: `MMM DD HH:MM:SS hostname process[PID]: message` (general system messages)
- **Auth**: SSH authentication attempts with user, IP, port, outcome
- **Kernel**: System events (device attachment, filesystem mounting, CPU, memory)
- **Mail**: Postfix/sendmail/dovecot messages (connections, rejections, deliveries, authentication)
- **Cron**: Scheduled task execution logs (commands run by cron daemon)
- **Daemon**: Service-specific messages (Apache, Nginx, MySQL, PostgreSQL, etc.)
- **Boot**: System startup messages (systemd initialization, service startup)
- **Package Manager**: APT/YUM/DPKG operations (install, upgrade, remove, dependency resolution)

## Dependencies

### Python Libraries
- `faker>=18.0`: Generates realistic fake names, IPs, usernames, timestamps

### System Tools
- `git`: For Cowrie repository cloning
- `python3`: 3.8+
- `createfs`: Provided by Cowrie (auto-installed)

## Troubleshooting

### "pip is required but not installed"
The script tries to bootstrap pip via `ensurepip`. If this fails:
```bash
# Manually install pip in the venv
python3 -m venv ~/.cowrie-src/venv
source ~/.cowrie-src/venv/bin/activate
python3 -m ensurepip --upgrade
pip install -r /path/to/cowrie/requirements.txt
```

### "createfs not found"
Ensure Cowrie installation completed successfully:
```bash
~/.cowrie-src/venv/bin/createfs --help
```

### Large filesystem capture taking too long
For very large golden images, reduce filesystem depth during capture via modification of `createfs` call in script.

## License



## References

- [Cowrie Honeypot](https://github.com/cowrie/cowrie) - GitHub repository
- [Cowrie Documentation](https://cowrie.readthedocs.io/) - Official docs
- [Faker Library](https://faker.readthedocs.io/) - Fake data generation

