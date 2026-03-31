# Script Pipeline System

Designed to be used together with **OFM** (file manager) as a lightweight way to run scripts like built-in tools.

---

## Why backends?

Scripts run inside isolated environments:

- **micromamba (default)** — fast, portable, no activation  
- **conda** — useful if you already depend on existing environments  

You can switch backend in `epy.bat`.

---

## Running scripts

Main entry point:

```
epy script.py
```

---

## Ways to run

### 1. CLI (default)

Run with arguments. Uses default values if not provided.

```
epy script.py --param value
```

---

### 2. Aliases

Wrap scripts as commands using `.cmd` files and PATH.

```
tree
```

---

### 3. Interactive mode

Hold **Left Ctrl** while running to open UI and override parameters before execution.

---

### 4. From OFM panel

Scripts can be triggered directly from OFM, using current directory / selection as context.

---

## Philosophy

- Scripts behave like CLI tools  
- No global dependencies  
- Minimal setup  
- Works both standalone and inside OFM
