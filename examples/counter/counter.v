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
endmodule