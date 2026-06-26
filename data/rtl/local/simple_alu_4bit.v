module simple_alu_4bit (
    input  [3:0] a, b,
    input  [1:0] op,
    output reg [3:0] result,
    output reg       zero
);
    always @(*) begin
        case (op)
            2'b00: result = a + b;
            2'b01: result = a - b;
            2'b10: result = a & b;
            2'b11: result = a | b;
        endcase
        zero = (result == 4'b0);
    end
endmodule