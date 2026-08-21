# Sample testbench for the Tiny Tapeout Kraken mini PIO tile

Uses [cocotb](https://docs.cocotb.org/en/stable/) plus a [pioasm](https://github.com/raspberrypi/pico-sdk/tree/master/tools/pioasm)-compiled
`hello_world.pio` program loaded through the pin-config protocol.

## How to run

Assemble the PIO program (needs `pioasm` on `PATH`, or macOS pico-sdk-tools):

```sh
make assemble
```

RTL simulation (assembles first if the hex is missing/out of date):

```sh
make -B
```

Gate-level simulation (after hardening): copy the generated netlist to
`gate_level_netlist.v`, then:

```sh
make -B GATES=yes
```

## What the test checks

1. `hello_world.pio` assembles to the expected SET-pin opcodes (`0xE101`, `0xE100`).
2. Config-mode pin loader writes those words into IMEM and sets wrap / SET_COUNT.
3. With the SM enabled, `uo[0]` produces a 50% square wave: `1,1,0,0,...`.

## Viewing waveforms

```sh
gtkwave tb.fst tb.gtkw
# or
surfer tb.fst
```
