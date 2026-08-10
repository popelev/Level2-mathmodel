# Lab SSH workflow (Windows → Ubuntu VM)

## Host

| Item | Value |
|------|--------|
| SSH alias | `level2-vm` |
| IP | `192.168.157.128` |
| User | `level2` |
| OS | Ubuntu (Docker + Jenkins) |

Configure `~/.ssh/config` on Windows (example):

```
Host level2-vm
  HostName 192.168.157.128
  User level2
  IdentityFile ~/.ssh/id_ed25519
```

## Roles

- **Windows**: edit code in this repo (`C:\Users\Admin\source\Level2-mathmodel`).
- **VM**: pull, run Docker tests/smoke, Jenkins Multibranch job `level2-mathmodel`.

## Safety vs Level2

- Use image/container name **`level2-mathmodel`** only.
- Host port **8090** (never 8080/8081 used by Level2).
- Join external Docker network **`smoke_default`** as a **client** (Level2 collector already there).
- Never `docker image prune` / `rmi` for `level2-collector*` or Jenkins images.
- Never `docker compose down` on Level2 projects.

## Helpers

From Windows (Git Bash / PowerShell with OpenSSH):

```bash
# Connectivity
scripts/lab/ssh-check.sh

# Clone or pull on VM to ~/Level2-mathmodel
scripts/lab/vm-pull.sh

# Engine pytest via Docker on VM
scripts/lab/vm-test.sh

# Compose config + network check (no disruptive down)
scripts/lab/vm-smoke.sh
```

Manual one-liner pattern:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm 'hostname && docker network inspect smoke_default >/dev/null && echo OK'
```

## First-time VM clone

```bash
ssh level2-vm 'git clone https://github.com/popelev/Level2-mathmodel.git ~/Level2-mathmodel'
```

If the remote is empty until Wave 0 is pushed, push from Windows first, then pull on the VM.
