module logical_shift_unit_8bit (
    input  [7:0] data,
    input  [2:0] shamt,
    input        direction,  // 0=left, 1=right
    output [7:0] result
);
    assign result = direction ? (data >> shamt) : (data << shamt);
endmodule