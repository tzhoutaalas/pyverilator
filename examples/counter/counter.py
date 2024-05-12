from pyverilator import PyVerilator

def main():
    sim = PyVerilator.build('counter.v')

    sim.start_vcd_trace('sim.vcd')

    # tick the automatically detected clock
    sim.clock.tick()

    # set rst back to 0
    sim.io.rst = 0

    # check out when en = 0
    sim.io.en = 0
    curr_out = sim.io.out

    # sim.io is a pyverilator.Collection, accessing signals by attribute or
    # dictionary syntax returns a SignalValue object which inherits from int.
    # sim.io.out can be used just like an int in most cases, and it has extra
    # features like being able to add it to gtkwave with
    # sim.io.out.send_to_gtkwave(). To just get the int value, you can call
    # sim.io.out.value
    print('sim.io.out = ' + str(curr_out))

    # check out when en = 1
    sim.io.en = 1
    curr_out = sim.io.out
    print('sim.io.out = ' + str(curr_out))

    sim.clock.tick()

    # check out after ticking clock
    curr_out = sim.io.out
    print('sim.io.out = ' + str(curr_out))

if __name__ == "__main__":
	main()
