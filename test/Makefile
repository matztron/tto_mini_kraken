# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src

# Match info.yaml source_files (package first for SystemVerilog).
PROJECT_SOURCES = \
  kraken_pkg.sv \
  kraken_alu.sv \
  kraken_decode.sv \
  kraken_fifo.sv \
  kraken_imem.sv \
  kraken_pc.sv \
  kraken_pins.sv \
  kraken_regfile.sv \
  kraken_sm.sv \
  kraken_tt_cfg.sv \
  kraken_tt_loader.sv \
  tt_um_kraken_mini.sv \
  project.v

# Locate Raspberry Pi pioasm (override: make PIOASM=/path/to/pioasm).
ifeq ($(origin PIOASM),undefined)
  ifneq ($(wildcard /Applications/pico-sdk-tools/pioasm/pioasm),)
    PIOASM := /Applications/pico-sdk-tools/pioasm/pioasm
  else
    PIOASM := pioasm
  endif
endif

# Keep cocotb's sim as the default goal (do not put other targets first).
.DEFAULT_GOAL := sim

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))
# SystemVerilog (packages, logic, etc.)
COMPILE_ARGS    += -g2012

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DSIM
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/art_stub.v
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: assemble check-pioasm

check-pioasm:
	@command -v $(PIOASM) >/dev/null 2>&1 || { \
		echo "error: pioasm not found (PIOASM=$(PIOASM))"; \
		echo "  export PATH=\"/Applications/pico-sdk-tools/pioasm:\$$PATH\""; \
		echo "  or: make PIOASM=/path/to/pioasm"; \
		exit 1; \
	}

assemble: check-pioasm
	mkdir -p generated
	$(PIOASM) -o hex hello_world.pio generated/hello_world.hex

# Ensure the pioasm hex exists before simulation (regenerate when .pio changes).
generated/hello_world.hex: hello_world.pio
	$(MAKE) assemble

# Hook assemble so local/CI runs always use a pioasm-built program.
sim: generated/hello_world.hex
