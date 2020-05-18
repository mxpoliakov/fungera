# Fungera: A two-dimensional evolution simulator
### Organism structure
- Main memory block
- Child memory block (optional)
- Instruction pointer
- Delta (direction)
- 4 general purpose registers
- A stack of 8 values
### Instruction set
| Symbol | Max ops | Description                                     | Type        |
|--------|---------|-------------------------------------------------|-------------|
| `.`      | 0       | Template constructor                            | Template    |
| `:`      | 0       | Template constructor                            | Template    |
| `a`      | 0       | Register modifier                               | Register    |
| `b`      | 0       | Register modifier                               | Register    |
| `c`      | 0       | Register modifier                               | Register    |
| `d`      | 0       | Register modifier                               | Register    |
| `^`      | 0       | Direction modifier (up)                         | Direction   |
| `v`      | 0       | Direction modifier (down)                       | Direction   |
| `>`      | 0       | Direction modifier (right)                      | Direction   |
| `<`      | 0       | Direction modifier (left)                       | Direction   |
| `x`      | 0       | Operation modifier                              | Operation   |
| `y`      | 0       | Operation modifier                              | Operation   |
| `&`      | 2+      | Find template, put its address in register      | Matching    |
| `?`      | 4       | If not zero                                     | Conditional |
| `0`      | 1       | Put [0, 0] vector into the register             | Arithmetic  |
| `1`      | 1       | Put [1, 1] vector into the register             | Arithmetic  |
| `-`      | 2       | Decrement value in register                     | Arithmetic  |
| `+`      | 2       | Increment value in register                     | Arithmetic  |
| `~`      | 3       | Subtract registers and store result in register | Arithmetic  |
| `W`      | 2       | Write instruction from register to address      | Replication |
| `L`      | 2       | Load instruction from address to register       | Replication |
| `@`      | 2       | Allocate child memory of size                   | Replication |
| `$`      | 0       | Split child organism                            | Replication |
| `S`      | 1       | Push value from register into the stack         | Stack       |
| `P`      | 1       | Pop value of register into the stack            | Stack       |

### Running Fungera
At least Python 3.7 is required to run Fungera. Once it is installed, running Fungera is simple. 
```
python -m pip install -r requirements.txt
python fungera.py --name "Simulation 1"
```

### TUI controls
| Key                | Action                                              |
|--------------------|-----------------------------------------------------|
| <kbd>space</kbd>   | Start/pause simulation                              |
| <kbd>c</kbd>       | Advance 1 cycle (only if paused) |
| <kbd>&#8593;</kbd> | Move memory view up                                 |
| <kbd>&#8595;</kbd> | Move memory view down                               |
| <kbd>&#8592;</kbd> | Move memory view left                               |
| <kbd>&#8594;</kbd> | Move memory view right                              |
| <kbd>d</kbd>       | Select next organism                                |
| <kbd>a</kbd>       | Select previous organism                            |
| <kbd>p</kbd>       | Save simulation                                     |
| <kbd>l</kbd>       | Load last saved simulation                          |
| <kbd>m</kbd>       | Toogle minimal mode                                 |