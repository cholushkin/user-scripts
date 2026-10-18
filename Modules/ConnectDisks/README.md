# ConnectDisks

A plain Windows batch script (not an `epy`/`BaseScript` tool — no interactive mode, no
presets) that maps network shares from an OMV (OpenMediaVault) NAS to local drive
letters using `subst`.

## Quick Start

Run it directly, with no launcher involved:

```
Modules\ConnectDisks\connect-omv-disks.cmd
```

## What it does

```cmd
subst K: \\VAULT\Vol1disk
subst M: \\VAULT\Vol2disk
subst N: \\VAULT\Vol3disk
```

Maps:

| Drive | NAS share |
| --- | --- |
| `K:` | `\\VAULT\Vol1disk` |
| `M:` | `\\VAULT\Vol2disk` |
| `N:` | `\\VAULT\Vol3disk` |

## Notes

- `subst` mappings do not survive a reboot — re-run the script after restarting, or
  schedule it (e.g. as a logon task) if you want it to persist automatically.
- Edit the drive letters or UNC paths directly in `connect-omv-disks.cmd` if your NAS
  hostname (`VAULT`) or share layout differs.
- Requires the `\\VAULT\...` shares to be reachable (NAS powered on, on the same
  network) before running.
