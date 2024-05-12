
    module multiply_accumulate (
            clk,
            rst_n,
            in_a,
            in_b,
            enable,
            clear,
            out);
        input        clk;
        input        rst_n;
        input [15:0] in_a;
        input [15:0] in_b;
        input        enable;
        input        clear;
        output [31:0] out;

        reg [15:0] operand_a;
        reg [15:0] operand_b;
        reg        operands_valid;

        reg [31:0] mul_result;
        reg        mul_result_valid;

        reg [31:0] accumulator;

        always @(posedge clk) begin
            if (rst_n == 0) begin
                operands_valid <= 0;
                mul_result_valid <= 0;
                accumulator <= 0;
            end else begin
                if (clear) begin
                    operands_valid <= 0;
                    mul_result_valid <= 0;
                    accumulator <= 0;
                end else begin
                    operands_valid <= enable;
                    mul_result_valid <= operands_valid;

                    if (enable) begin
                        operand_a <= in_a;
                        operand_b <= in_b;
                        operands_valid <= 1;
                    end else begin
                        operands_valid <= 0;
                    end

                    if (operands_valid) begin
                        mul_result <= operand_a * operand_b;
                        mul_result_valid <= 1;
                    end else begin
                        mul_result_valid <= 0;
                    end

                    if (mul_result_valid) begin
                        accumulator <= accumulator + mul_result;
                    end
                end
            end
        end

        assign out = accumulator;
    endmodule