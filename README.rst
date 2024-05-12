PyVerilator
===========

This package provides a wrapper to generate and use verilator
hardware models in python.

Usage
-----

The full code for this and other examples can be found in the examples folder
of the git repository:

    $ cd examples/counter
    $ python3 counter.py

Assume you have the following verilog module stored in ``counter.v``.

.. code:: verilog

    module counter (
            input        clk,
            input        rst,
            input        en,
            output [7:0] out
        );
        reg [7:0] count_reg;
        wire [7:0] next_count_reg;
        assign next_count_reg = (en == 1) ? count_reg + 1 : count_reg;
        assign out = next_count_reg;
        always @(posedge clk) begin
            if (rst == 1) count_reg <= 0;
            else          count_reg <= next_count_reg;
        end
    endmodule'''

Then you can use ``pyverilator`` to simulate this module using verilator in
python.

.. code:: python
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

