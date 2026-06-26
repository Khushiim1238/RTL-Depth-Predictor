module simple_alu_8bit (
    input  [7:0] a, b,
    input  [2:0] op,
    output reg [7:0] result,
    output reg       carry, zero, negative
);
    always @(*) begin
        carry    = 1'b0;
        case (op)
            3'b000: {carry, result} = a + b;
            3'b001: {carry, result} = a - b;
            3'b010: result = a & b;
            3'b011: result = a | b;
            3'b100: result = a ^ b;
            3'b101: result = ~a;
            3'b110: result = a << 1;
            3'b111: result = a >> 1;
        endcase
        zero     = (result == 8'b0);
        negative = result[7];
    end
endmodule