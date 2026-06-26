module magnitude_comparator_8bit (
    input  [7:0] a, b,
    output       a_gt_b, a_eq_b, a_lt_b
);
    assign a_gt_b = (a > b);
    assign a_eq_b = (a == b);
    assign a_lt_b = (a < b);
endmodule