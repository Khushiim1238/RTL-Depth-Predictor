module multiplier_with_accumulate_8bit (
    input  [7:0] a, b,
    input  [15:0] acc_in,
    output [15:0] result
);
    assign result = acc_in + (a * b);
endmodule