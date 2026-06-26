module abs_difference_8bit (
    input  [7:0] a, b,
    output [7:0] abs_diff
);
    assign abs_diff = (a >= b) ? (a - b) : (b - a);
endmodule