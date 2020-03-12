# Fungera: A two-dimensional evolution simulator
### Organism structure
- Main memory block
- Child memory block (optional)
- Instruction pointer
- Delta (direction)
- 4 general purpose registers
- A stack of 8 values
### Instruction set
|Symbol |Arguments |Description                  |
|:------|:---------|:----------------------------|
|`.`    |0         |Template constructor         |
|`:`    |0         |Template constructor         |
|`a`    |0         |Register modifier            |
|`b`    |0         |Register modifier            |
|`c`    |0         |Register modifier            |
|`d`    |0         |Register modifier            |
|`^`    |0         |Direction modifier (up)      |
|`v`    |0         |Direction modifier (down)    |
|`<`    |0         |Direction modifier (left)    |
|`>`    |0         |Direction modifier (right)   |
|`x`    |0         |Operation modifier           |
|`y`    |0         |Operation modifier           |