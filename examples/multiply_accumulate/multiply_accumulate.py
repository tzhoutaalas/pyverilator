import os
import pyverilator

# setup build directory and cd to it
# build_dir = os.path.join(os.path.dirname(__file__), 'build', os.path.basename(__file__))
# os.makedirs(build_dir, exist_ok = True)
# os.chdir(build_dir)

sim = pyverilator.PyVerilator.build('multiply_accumulate.v')

# setup a few functions
def tick_clock():
    sim.io.clk = 0
    sim.io.clk = 1

def reset():
    sim.io.rst_n = 0
    tick_clock()
    sim.io.rst_n = 1
    sim.io.enable = 0
    sim.io.clear = 0

def input_and_tick_clock( a, b ):
    sim.io.in_a = a
    sim.io.in_b = b
    sim.io.enable = 1
    sim.io.clear = 0
    tick_clock()
    sim.io.enable = 0

def clear_and_tick_clock():
    sim.io.enable = 0
    sim.io.clear = 1
    tick_clock()
    sim.io.clear = 0

sim.start_gtkwave()
sim.send_to_gtkwave(sim.io)
sim.send_to_gtkwave(sim.internals)

reset()

commands = ['tick_clock()',
            'tick_clock()',
            'tick_clock()',
            'input_and_tick_clock(1, 1)',
            'tick_clock()',
            'tick_clock()',
            'input_and_tick_clock(1, 1)',
            'tick_clock()',
            'tick_clock()',
            'input_and_tick_clock(1, 1)',
            'input_and_tick_clock(1, 1)',
            'input_and_tick_clock(1, 1)',
            'tick_clock()',
            'tick_clock()',
            'clear_and_tick_clock()',
            'input_and_tick_clock(2, 2)',
            'input_and_tick_clock(3, -1)',
            'input_and_tick_clock(3, 3)',
            'input_and_tick_clock(-2, 2)',
            'input_and_tick_clock(4, 3)',
            'input_and_tick_clock(-2, -1)',
            'input_and_tick_clock(-3, -2)',
            'input_and_tick_clock(3, -7)',
            'tick_clock()',
            'tick_clock()']

print('Press enter to simulate entering a command (there are %d commands in this demo)' % len(commands))
for c in commands:
    # wait for enter
    input()
    print('>> ' + c, end = '')
    eval(c)
# wait for enter one last time
input()
print('Done! Closing GTKWave...')

sim.stop_gtkwave()

sim.stop_vcd_trace()
