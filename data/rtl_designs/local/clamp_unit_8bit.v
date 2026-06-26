module clamp_unit_8bit (
    input  [7:0] data,
    input  [7:0] lo, hi,
    output [7:0] clamped
);
    assign clamped = (data < lo) ? lo :
                     (data > hi) ? hi : data;
endmodule