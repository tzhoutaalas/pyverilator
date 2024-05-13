import re

def header_cpp(top_module):
    s = """#include <cstddef>
#include <iostream>
#include "verilated.h"
#include "verilated_vcd_c.h"
#include "{module_filename}.h"
#define UINT32_TO_UINT32(u) (*((uint32_t *)&(u)))
#define UINT64_TO_UINT64(u) (*((uint64_t *)&(u)))
    """.format(module_filename='V' + top_module)
    return s

def var_declaration_cpp(top_module, inputs, outputs, internal_signals, json_data):
    s = """// pyverilator defined values
// first declare variables as extern
extern const char* _pyverilator_module_name;
extern const uint32_t _pyverilator_num_inputs;
extern const char* _pyverilator_inputs[];
extern const uint32_t _pyverilator_input_widths[];
extern const uint32_t _pyverilator_num_outputs;
extern const char* _pyverilator_outputs[];
extern const uint32_t _pyverilator_output_widths[];
extern const uint32_t _pyverilator_num_internal_signals;
extern const char* _pyverilator_internal_signals[];
extern const uint32_t _pyverilator_internal_signal_widths[];
extern const uint32_t _pyverilator_num_rules;
extern const char* _pyverilator_rules[];
extern const char* _pyverilator_json_data;
// now initialize the variables
const char* _pyverilator_module_name = "{top_module}";
const uint32_t _pyverilator_num_inputs = {nb_inputs};
const char* _pyverilator_inputs[] = {{{name_inputs}}};
const uint32_t _pyverilator_input_widths[] = {{{size_inputs}}};

const uint32_t _pyverilator_num_outputs = {nb_outputs};
const char* _pyverilator_outputs[] = {{{name_outputs}}};
const uint32_t _pyverilator_output_widths[] = {{{size_outputs}}};

const uint32_t _pyverilator_num_internal_signals = {nb_internals};
const char* _pyverilator_internal_signals[] = {{{name_internals}}};
const uint32_t _pyverilator_internal_signal_widths[] = {{{size_internals}}};

const char* _pyverilator_json_data = {json_data};

// this is required by verilator for verilog designs using $time
// main_time is incremented in eval
double main_time = 0;

// What to call when $finish is called
typedef void (*vl_finish_callback)(const char* filename, int line, const char* hier);
vl_finish_callback vl_user_finish = NULL;
    """.format(
        top_module = top_module,
        nb_inputs=len(inputs),
        name_inputs=",".join(map(lambda input: '"' + input[0] + '"', inputs)),
        size_inputs=",".join(map(lambda input: str(input[1]), inputs)),
        nb_outputs=len(outputs),
        name_outputs=",".join(map(lambda output: '"' + output[0] + '"', outputs)),
        size_outputs=",".join(map(lambda output: str(output[1]), outputs)),
        nb_internals=len(internal_signals),
        name_internals=",".join(map(lambda internal: '"' + internal[0] + '"', internal_signals)),
        size_internals=",".join(map(lambda internal: str(internal[1]), internal_signals)),
        json_data=json_data if json_data else "null")
    return s

def function_definitions_cpp(top_module, inputs, outputs, internal_signals, json_data):
    constant_part = """double sc_time_stamp() {{
return main_time;
}}
void vl_finish (const char* filename, int linenum, const char* hier) VL_MT_UNSAFE {{
    if (vl_user_finish) {{
       (*vl_user_finish)(filename, linenum, hier);
    }} else {{
        // Default implementation
        VL_PRINTF("- %s:%d: Verilog $finish\\n", filename, linenum);  // Not VL_PRINTF_MT, already on main thread
        if (Verilated::gotFinish()) {{
            VL_PRINTF("- %s:%d: Second verilog $finish, exiting\\n", filename, linenum);  // Not VL_PRINTF_MT, already on main thread
            Verilated::flushCall();
            exit(0);
        }}
        Verilated::gotFinish(true);
    }}
}}
// function definitions
// helper functions for basic verilator tasks
extern "C" {{ //Open an extern C closed in the footer
{module_filename}* construct() {{
    Verilated::traceEverOn(true);
    {module_filename}* top = new {module_filename}();
    return top;
}}
int eval({module_filename}* top) {{
    top->eval();
    main_time++;
    return 0;
}}
int destruct({module_filename}* top) {{
    if (top != nullptr) {{
        delete top;
        top = nullptr;
    }}
    return 0;
}}
VerilatedVcdC* start_vcd_trace({module_filename}* top, const char* filename) {{
    VerilatedVcdC* tfp = new VerilatedVcdC;
    top->trace(tfp, 99);
    tfp->open(filename);
    return tfp;
}}
int add_to_vcd_trace(VerilatedVcdC* tfp, int time) {{
    tfp->dump(time);
    return 0;
}}
int flush_vcd_trace(VerilatedVcdC* tfp) {{
    tfp->flush();
    return 0;
}}
int stop_vcd_trace(VerilatedVcdC* tfp) {{
    tfp->close();
    return 0;
}}
bool get_finished() {{
    return Verilated::gotFinish();
}}
void set_finished(bool b) {{
    Verilated::gotFinish(b);
}}
void set_vl_finish_callback(vl_finish_callback callback) {{
    vl_user_finish = callback;
}}
void set_command_args(int argc, char** argv) {{
    Verilated::commandArgs(argc, argv);
}}
""".format(module_filename='V' + top_module)

    def port_name(port):
        return re.sub(r'\(|\&|\[.*?\]|\)', '', port[0])
    def num_slices(port):
        start_index = port[0].find('[')
        end_index = port[0].find(']', start_index)
        if start_index != -1 and end_index != -1:
            return int(port[0][start_index + 1:end_index])
        return 1

    sample_output_functions = ""
    single_slice_ports = []
    for port in outputs + inputs + internal_signals:
        # Flat Ports
        if num_slices(port) == 1:
            single_slice_ports.append(port)
            sample_output_functions += (
"""uint32_t get_{port_name}_element({module_filename}* top, int index) {{
    return top->{port_name};
}}
""" if port[1] <= 32 else 
"""uint64_t get_{port_name}_element({module_filename}* top, int index) {{
    return top->{port_name};
}}
""" if port[1] <= 64 else 
"""uint32_t get_{port_name}_element({module_filename}* top, int index) {{
    return top->{port_name}[index];
}}
""").format(module_filename='V' + top_module, port_name=port_name(port))
            sample_output_functions += (
"""void sample_{port_name}({module_filename}* top, void* out, const int num_elements) {{
    for (int i = 0; i < num_elements; i+=2) {{
        uint64_t val = get_{port_name}_element(top, i);
        ((uint32_t *)out)[i] = val & 0xFFFFFFFF;
        ((uint32_t *)out)[i+1] = (val >> 32) & 0xFFFFFFFF;
    }}
}}
""" if port[1] == 64 else
"""void sample_{port_name}({module_filename}* top, void* out, const int num_elements) {{
    for (int i = 0; i < num_elements; i++) {{
        ((uint32_t *)out)[i] = get_{port_name}_element(top, i);
    }}
}}
""").format(module_filename='V' + top_module, port_name=port_name(port))

        # Multi-dimensional Ports
        else:
            sample_output_functions += (
"""uint32_t get_{port_name}_element({module_filename}* top, int slice, int index) {{
    return top->{port_name}[slice];
}}
""" if port[1] <= 32 else 
"""uint64_t get_{port_name}_element({module_filename}* top, int slice, int index) {{
    return top->{port_name}[slice];
}}
""" if port[1] <= 64 else 
"""uint32_t get_{port_name}_element({module_filename}* top, int slice, int index) {{
    return top->{port_name}[slice][index];
}}
""").format(module_filename='V' + top_module, port_name=port_name(port))
            sample_output_functions += (
"""void sample_{port_name}({module_filename}* top, void* out, const int num_elements) {{
    int i = 0;
    for (int slice = 0; slice < {num_slices}; slice++) {{
        for (int j = 0; j < num_elements / {num_slices}; i+=2, j+=2) {{
            uint64_t val = get_{port_name}_element(top, slice, j);
            ((uint32_t *)out)[i] = val & 0xFFFFFFFF;
            ((uint32_t *)out)[i+1] = (val >> 32) & 0xFFFFFFFF;
        }}
    }}
}}
void sample_{port_name}_element({module_filename}* top, void* out, const int slice, const int index) {{
    uint64_t val = get_{port_name}_element(top, slice, index);
    ((uint32_t *)out)[0] = val & 0xFFFFFFFF;
    ((uint32_t *)out)[1] = (val >> 32) & 0xFFFFFFFF;
}}
""" if port[1] == 64 else
"""void sample_{port_name}({module_filename}* top, void* out, const int num_elements) {{
    int i = 0;
    for (int slice = 0; slice < {num_slices}; slice++) {{
        for (int j = 0; j < num_elements / {num_slices}; i++, j++) {{
            ((uint32_t *)out)[i] = get_{port_name}_element(top, slice, j);
        }}
    }}
}}
void sample_{port_name}_element({module_filename}* top, void* out, const int slice, const int index) {{
    ((uint32_t *)out)[0] = get_{port_name}_element(top, slice, index);
}}
""").format(module_filename='V' + top_module, num_slices=num_slices(port), port_name=port_name(port))

    drive_input_functions = ""
    single_slice_inputs = []
    for port in inputs:
        # Flat Ports
        if num_slices(port) == 1:
            single_slice_inputs.append(port)
            drive_input_functions += (
"""void set_{port_name}_element({module_filename}* top, int32_t val, int index) {{
    top->{port_name} = UINT32_TO_UINT32(val);
}}
""" if port[1] <= 32 else 
"""void set_{port_name}_element({module_filename}* top, int64_t val, int index) {{
    top->{port_name} = UINT64_TO_UINT64(val);
}}
""" if port[1] <= 64 else 
"""void set_{port_name}_element({module_filename}* top, int32_t val, int index) {{
    top->{port_name}[index] = UINT32_TO_UINT32(val);
}}
""").format(module_filename='V' + top_module, port_name=port_name(port))
            drive_input_functions += (
"""void drive_{port_name}({module_filename}* top, const void* in, const int num_elements) {{
    for (int i = 0; i < num_elements; i+=2) {{
        int64_t hi = ((int32_t *)in)[i+1] & 0xFFFFFFFF;
        int64_t lo = ((int32_t *)in)[i] & 0xFFFFFFFF;
        set_{port_name}_element(top, ((hi<<32)|lo), i);
    }}
}}
""" if port[1] == 64 else """
void drive_{port_name}({module_filename}* top, const void* in, const int num_elements) {{
    for (int i = 0; i < num_elements; i++) {{
        set_{port_name}_element(top, ((int32_t *)in)[i], i);
    }}
}}
""").format(module_filename='V' + top_module, port_name=port_name(port))
            drive_input_functions += """
void drive_{port_name}_element({module_filename}* top, const void* in, int index) {{
    set_{port_name}_element(top, *((int32_t *)in), index);
}}
""".format(module_filename='V' + top_module, port_name=port_name(port))

        # Multi-dimensional Ports
        else:
            drive_input_functions += (
"""void set_{port_name}_element({module_filename}* top, int32_t val, int slice, int index) {{
    top->{port_name}[slice] = UINT32_TO_UINT32(val);
}}
""" if port[1] <= 32 else 
"""void set_{port_name}_element({module_filename}* top, int64_t val, int slice, int index) {{
    top->{port_name}[slice] = UINT64_TO_UINT64(val);
}}
""" if port[1] <= 64 else 
"""void set_{port_name}_element({module_filename}* top, int32_t val, int slice, int index) {{
    top->{port_name}[slice][index] = UINT32_TO_UINT32(val);
}}
""").format(module_filename='V' + top_module, num_slices=num_slices(port), port_name=port_name(port))
            drive_input_functions += (
"""void drive_{port_name}({module_filename}* top, const void* in, int num_elements) {{
    int i = 0;
    for (int slice = 0; slice < {num_slices}; slice++) {{
        for (int j = 0; j < num_elements / {num_slices}; i+=2, j+=2) {{
            int64_t hi = ((int32_t *)in)[i+1] & 0xFFFFFFFF;
            int64_t lo = ((int32_t *)in)[i] & 0xFFFFFFFF;
            set_{port_name}_element(top, ((hi<<32)|lo), slice, j);
        }}
    }}
}}""" if port[1] == 64 else
"""void drive_{port_name}({module_filename}* top, const void* in, int num_elements) {{
    int i = 0;
    for (int slice = 0; slice < {num_slices}; slice++) {{
        for (int j = 0; j < num_elements / {num_slices}; i++, j++) {{
            set_{port_name}_element(top, ((int32_t *)in)[i], slice, j);
        }}
    }}
}}""").format(module_filename='V' + top_module, num_slices=num_slices(port), port_name=port_name(port))
            drive_input_functions += """
void drive_{port_name}_element({module_filename}* top, const void* in, int slice, int index) {{
    set_{port_name}_element(top, *((int32_t *)in), slice, index);
}}
""".format(module_filename='V' + top_module, num_slices=num_slices(port), port_name=port_name(port))

    # Setters and getters can only be used for 1D ports
    get_functions = "\n".join(map(lambda port: (
        "uint32_t get_{portname}({module_filename}* top, int word)"
        "{{ return top->{portname}[word];}}" if port[1] > 64 else (
            "uint64_t get_{portname}({module_filename}* top)"
            "{{return top->{portname};}}" if port[1] > 32 else
            "uint32_t get_{portname}({module_filename}* top)"
            "{{return top->{portname};}}")).format(module_filename='V' + top_module, portname=port_name(port)),
                                  single_slice_ports))
    set_functions = "\n".join(map(lambda port: (
        "int set_{portname}({module_filename}* top, int word, uint64_t new_value)"
        "{{ top->{portname}[word] = new_value; return 0;}}" if port[1] > 64 else (
            "int set_{portname}({module_filename}* top, uint64_t new_value)"
            "{{ top->{portname} = new_value; return 0;}}" if port[1] > 32 else
            "int set_{portname}({module_filename}* top, uint32_t new_value)"
            "{{ top->{portname} = new_value; return 0;}}")).format(module_filename='V' + top_module, portname=port_name(port)),
                                  single_slice_inputs))
    footer = "}"
    comments = "\n// inputs \n// " + "\n// ".join(map(lambda port: f"{port}", inputs))
    comments += "\n// outputs \n// " + "\n// ".join(map(lambda port: f"{port}", outputs))
    comments += "\n// internal \n// " + "\n// ".join(map(lambda port: f"{port}", internal_signals))
    return "\n".join([constant_part, sample_output_functions, drive_input_functions, get_functions, set_functions, footer, comments])


def template_cpp(top_module, inputs, outputs, internal_signals, json_data):
    return "\n".join([header_cpp(top_module),
                      var_declaration_cpp(top_module, inputs, outputs, internal_signals, json_data),
                      function_definitions_cpp(top_module, inputs, outputs, internal_signals, json_data)])
