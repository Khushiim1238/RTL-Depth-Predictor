module barrel_shifter_arith_16bit (
    input signed [15:0] data,
    input [3:0]         shamt,
    input               left_right,
    output reg [15:0]   out
);
    always @(*) begin
        if (left_right)
            out = data << shamt;
        else
            out = $signed(data) >>> shamt;
    end
endmodule