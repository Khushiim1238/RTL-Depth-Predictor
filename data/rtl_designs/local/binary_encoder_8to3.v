module binary_encoder_8to3 (
    input  [7:0] in,
    output reg [2:0] out
);
    always @(*) begin
        casez (in)
            8'b10000000: out = 3'd7;
            8'b01000000: out = 3'd6;
            8'b00100000: out = 3'd5;
            8'b00010000: out = 3'd4;
            8'b00001000: out = 3'd3;
            8'b00000100: out = 3'd2;
            8'b00000010: out = 3'd1;
            default:     out = 3'd0;
        endcase
    end
endmodule