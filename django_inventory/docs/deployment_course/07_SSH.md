# 07 — SSH

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [06 — Linux Basics](06_Linux_Basics.md). Next: [08 — The File System](08_File_System.md).

# Purpose
My VPS has no monitor or keyboard — the only way in is over the network. **SSH (Secure Shell)** is that door: an encrypted remote login to the server's shell. This chapter is how to get in *safely* (keys, not passwords), how to harden the door so attackers can't, and how to use SSH **tunnels** to reach private services (like Postgres) without exposing them ([Ch 05](05_IP_Address_and_Ports.md)).

# The Problem
I need to run commands on a machine sitting in a data center thousands of km away, over the hostile internet, with total confidence that (a) nobody can eavesdrop, (b) I'm really talking to *my* server and not an impostor, and (c) attackers can't guess their way in. Telnet/FTP (old, plaintext) fail all three. SSH solves all three — but only if configured right. Bots scan the internet 24/7 hammering port 22 with password guesses; a password-only server is a matter of *when*, not *if*.

# Theory (from zero)

### What SSH is
SSH gives you an **encrypted terminal** on a remote machine. You type locally; commands run there; output comes back — all over an encrypted TCP connection to **port 22** ([Ch 05](05_IP_Address_and_Ports.md)). It's how you administer every Linux server.

### Passwords vs keys (use keys)
Two ways to prove who you are:
1. **Password** — guessable, brute-forceable, phishable. Bots try millions.
2. **Public-key (asymmetric) auth** — you generate a **key pair**: a **private key** (stays on your laptop, secret, never leaves) and a **public key** (copied to the server). Login works only if you hold the matching private key. Nothing brute-forceable travels; there's no password to steal. **This is the standard.**

How it works: the server, on connect, challenges you to prove you hold the private key matching a public key in its `~/.ssh/authorized_keys`. Math proves it without sending the secret. (Same asymmetric idea as TLS certs in [Ch 03](03_HTTP_HTTPS.md).)

### `known_hosts` — verifying the *server*
The first time you connect, SSH shows the server's **host key fingerprint** and asks "trust this?". It saves it in your `~/.ssh/known_hosts`. On later connects it checks the key matches — if it suddenly differs, SSH **refuses** and warns of a possible man-in-the-middle. (If you legitimately rebuilt the server, you remove the old line.)

### The SSH config file (quality-of-life)
`~/.ssh/config` lets you alias connections:
```
Host erp
    HostName 203.0.113.10
    User umesh
    IdentityFile ~/.ssh/id_ed25519
    Port 22
```
Then just `ssh erp`. Scripts (`deploy.sh`) become readable.

### Hardening the door (do this on the VPS)
In `/etc/ssh/sshd_config`:
- `PasswordAuthentication no` — keys only (kills brute-force).
- `PermitRootLogin no` — never log in as root directly; use a normal user + `sudo` ([Ch 06](06_Linux_Basics.md)).
- Optionally change the port or restrict source IPs; install `fail2ban` to auto-ban repeat offenders.
Then `sudo systemctl restart ssh` ([Ch 10](10_Systemd.md)).

### SSH tunnels (reach private services safely)
An SSH **tunnel** (port forward) carries another protocol *inside* the encrypted SSH connection. To use a DB GUI against production Postgres **without publishing 5432** ([Ch 05](05_IP_Address_and_Ports.md)):
```
ssh -L 5432:localhost:5432 erp
```
`-L 5432:localhost:5432` = "forward my laptop's `localhost:5432` to `localhost:5432` on the server." Point pgAdmin at `localhost:5432`; traffic rides the SSH channel; the DB stays private. (For a Dockerized DB, forward to the container: `-L 5432:db:5432` from a host with access, or expose it only on the server's loopback.)

# Real World Example (My ERP)
- I connect with `ssh erp` (using a `~/.ssh/config` alias + an **ed25519** key). My private key never leaves my laptop; the VPS has only my public key in `authorized_keys`.
- The VPS is hardened: **password auth off, root login off**. I log in as a normal user and `sudo` for Docker/admin.
- **Deploying** happens over SSH: I `ssh erp`, `cd` to the project, `git pull`, `docker compose ... up -d --build` (or run `deploy/deploy.sh`, which does the pre-deploy DB dump → pull → build → up). Every deploy command in [Ch 36](36_My_ERP_Deployment.md) is typed over this SSH session.
- **DB inspection** (when I must peek at production Postgres) uses an **SSH tunnel**, never a published 5432 — matching the RC1/[Ch 05](05_IP_Address_and_Ports.md) rule that data stores stay private.
- **Backups off-site** ([Ch 28](28_Backups.md)) and file copies use SSH's cousins `scp`/`rsync` over the same secure channel.

# Visual Diagram
```
  LAPTOP                                            VPS (203.0.113.10:22)
  ~/.ssh/id_ed25519       ── encrypted SSH ──►      ~/.ssh/authorized_keys
  (PRIVATE, never leaves)                            (your PUBLIC key)
        │  prove I hold the private key (math, no secret sent)              
        │  server proves its identity via host key ──► saved in known_hosts 
        ▼                                                                   
  ssh erp  →  umesh@erp-vps:~$   (a shell on the server)

  TUNNEL (reach private Postgres without opening 5432 to internet):
  laptop:5432  ══inside the SSH pipe══►  vps → db:5432
  point pgAdmin at localhost:5432        (DB never exposed publicly)

  hardened door:  PasswordAuthentication no  +  PermitRootLogin no  +  fail2ban
```

# Practical — how to inspect it (every command explained)
```bash
# 1. Generate a key pair on the LAPTOP (once). ed25519 = modern, short, strong.
ssh-keygen -t ed25519 -C "umesh-laptop"
#   creates ~/.ssh/id_ed25519 (PRIVATE — guard it) and id_ed25519.pub (public)
```
```bash
# 2. Copy the PUBLIC key to the server (enables key login)
ssh-copy-id umesh@203.0.113.10      # appends your .pub to the server's authorized_keys
```
```bash
# 3. Log in
ssh umesh@203.0.113.10              # first time: verify + accept host fingerprint
ssh erp                             # with a ~/.ssh/config alias
```
```bash
# 4. Run a single remote command without an interactive shell
ssh erp 'docker compose ps'         # runs on the server, prints locally
```
```bash
# 5. Copy files over SSH
scp ./local.txt erp:/home/umesh/    # copy a file up
rsync -avz ./dir/ erp:/home/umesh/dir/   # sync a directory (incremental)
```
```bash
# 6. Tunnel to private Postgres
ssh -L 5432:localhost:5432 erp      # then connect a DB tool to localhost:5432
```
```bash
# 7. On the server: verify hardening
sudo sshd -T | grep -Ei 'passwordauthentication|permitrootlogin'
#   expect: passwordauthentication no / permitrootlogin no
sudo systemctl status ssh           # is the SSH service running? ([Ch 10])
```

# Beginner Mistakes
- **Leaving password auth on.** Bots will brute-force port 22 relentlessly. Keys only + fail2ban.
- **Logging in as root.** Direct root over SSH = one compromised credential owns everything. Normal user + `sudo`.
- **Losing / not backing up the private key** — or worse, committing it to git. If it leaks, anyone is you; if you lose it with no other key on the server, you're locked out. Keep a backup key; guard `~/.ssh/`.
- **`chmod 777 ~/.ssh`** or a world-readable key — SSH *refuses* keys with loose permissions. Keep `~/.ssh` at `700` and keys at `600`.
- **Ignoring a changed host-key warning.** It might be a real MITM — or a rebuilt server. Understand *why* before deleting the `known_hosts` line.
- **Publishing 5432 "just to use pgAdmin."** Use a tunnel; never expose the DB ([Ch 05](05_IP_Address_and_Ports.md)).

# Interview Questions
**Junior — "Why use SSH keys instead of passwords?"** Keys use asymmetric crypto: the secret private key never leaves your machine and nothing brute-forceable is transmitted, so there's no password for bots to guess or steal — far stronger than a password.

**Junior — "What is `known_hosts` for?"** It records each server's host key so SSH can verify on later connections that you're talking to the same server, warning you about possible man-in-the-middle if the key changes.

**Mid — "How do you connect a local DB tool to production Postgres securely?"** An SSH local port-forward: `ssh -L 5432:localhost:5432 server`, then point the tool at `localhost:5432`. The DB port stays closed to the internet; the connection is tunneled through authenticated, encrypted SSH.

**Senior — "Harden SSH on a fresh Ubuntu VPS. What do you change and why?"** Add a normal sudo user + your public key; set `PasswordAuthentication no` (kill brute-force) and `PermitRootLogin no` (least privilege); restrict/allow port 22 in the firewall (ideally to known IPs); install `fail2ban` to auto-ban repeat offenders; keep the private key safe with a passphrase + agent. Restart `ssh` and confirm you can still log in *before* closing the old session.

**Staff — "A teammate's laptop with an authorized SSH key is stolen. Incident response?"** Immediately remove that public key from every server's `authorized_keys` (and any config-management source of truth), rotate any secrets that key could have reached, review auth logs (`/var/log/auth.log`) for logins from that key after theft, and if in doubt rebuild the box from a known-good image + restore data from backup ([Ch 40](40_Disaster_Recovery.md)). Longer term: short-lived certificates/SSH CA instead of static keys, and per-person keys (never shared) so revocation is surgical.

# Cheat Sheet
- **SSH = encrypted remote shell** to port 22. **Use keys, not passwords.**
- **Key pair:** private (laptop, secret, `600`) + public (server `~/.ssh/authorized_keys`). `ssh-keygen -t ed25519`, `ssh-copy-id`.
- **known_hosts** verifies the server identity (MITM protection).
- **`~/.ssh/config`** aliases (`ssh erp`). **Run remote cmd:** `ssh erp 'cmd'`. **Copy:** `scp`/`rsync`.
- **Tunnel private DB:** `ssh -L 5432:localhost:5432 erp` → tool at `localhost:5432`. Never publish 5432.
- **Harden:** `PasswordAuthentication no`, `PermitRootLogin no`, `fail2ban`. Verify with `sudo sshd -T`.
- **Permissions:** `~/.ssh` = 700, keys = 600, or SSH rejects them.

# My ERP Section
| Concept | In my ERP |
|---|---|
| How I reach the VPS | `ssh erp` (ed25519 key + `~/.ssh/config`) |
| Auth model | key-only; `PasswordAuthentication no`, `PermitRootLogin no` |
| Deploy transport | SSH → `git pull` + `docker compose up -d --build` / `deploy/deploy.sh` |
| Prod DB access | `ssh -L 5432:localhost:5432 erp` (tunnel; 5432 never published) |
| Off-site copy | `scp`/`rsync` over SSH; restic backups ([Ch 28](28_Backups.md)) |
| Auth logs | `/var/log/auth.log` on the VPS |

# Homework
1. `ssh-keygen -t ed25519 -C "me"` on your laptop. Inspect `~/.ssh/`: which file is private, which public? Check their permissions (`ls -l ~/.ssh`).
2. If you have any Linux box/VM, `ssh-copy-id` your key to it, then `ssh` in without a password. Note the first-time host-fingerprint prompt (that's `known_hosts` being written).
3. Write a `~/.ssh/config` `Host erp` block for your future VPS (fill in placeholders). What does `ssh erp` now save you typing?
4. Explain, in one sentence, how an SSH tunnel lets you use pgAdmin against production Postgres while keeping 5432 closed to the internet.
5. On a test box, set `PasswordAuthentication no`, restart ssh, and confirm with `sudo sshd -T | grep passwordauthentication`. Why must you verify key login works *before* logging out?

---

## Further Reading & Live Resources
- DigitalOcean — *SSH Essentials: Working with SSH Servers, Clients, and Keys*: https://www.digitalocean.com/community/tutorials/ssh-essentials-working-with-ssh-servers-clients-and-keys
- DigitalOcean — *How to Set Up SSH Keys on Ubuntu*: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-22-04
- Ubuntu Server docs — *OpenSSH*: https://ubuntu.com/server/docs/service-openssh
- Mozilla — *OpenSSH security guidelines* (hardening reference): https://infosec.mozilla.org/guidelines/openssh
- `ssh_config` / `sshd_config` manuals: https://man.openbsd.org/ssh_config and https://man.openbsd.org/sshd_config
- fail2ban docs (auto-ban brute-forcers): https://github.com/fail2ban/fail2ban/wiki
- SSH Academy — *SSH tunneling / port forwarding explained*: https://www.ssh.com/academy/ssh/tunneling
