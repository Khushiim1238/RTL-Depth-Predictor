module alu_16bit (
    input  [15:0] a, b,
    input  [3:0]  op,
    output reg [15:0] result,
    output reg        carry, overflow, zero, negative
);
    always @(*) begin
        carry    = 0;
        overflow = 0;
        case (op)
            4'b0000: {carry, result} = a + b;
            4'b0001: {carry, result} = a - b;
            4'b0010: result = a * b;
            4'b0011: result = a & b;
            4'b0100: result = a | b;
            4'b0101: result = a ^ b;
            4'b0110: result = ~a;
            4'b0111: result = a << b[3:0];
            4'b1000: result = a >> b[3:0];
            4'b1001: result = $signed(a) >>> b[3:0];
            4'b1010: result = (a > b) ? 16'd1 : 16'd0;
            4'b1011: result = (a == b) ? 16'd1 : 16'd0;
            4'b1100: result = (a < b) ? 16'd1 : 16'd0;
            4'b1101: result = a + 16'd1;
            4'b1110: result = a - 16'd1;
            4'b1111: result = 16'd0;
        endcase
        zero     = (result == 16'd0);
        negative = result[15];
    end
endmodule