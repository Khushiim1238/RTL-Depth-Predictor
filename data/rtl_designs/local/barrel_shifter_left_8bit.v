module barrel_shifter_left_8bit (
    input  [7:0] data,
    input  [2:0] shamt,
    output [7:0] out
);
    assign out = data << shamt;
endmodule