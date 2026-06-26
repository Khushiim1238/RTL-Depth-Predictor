module signed_comparator_8bit (
    input signed [7:0] a, b,
    output             a_gt_b, a_eq_b, a_lt_b
);
    assign a_gt_b = ($signed(a) > $signed(b));
    assign a_eq_b = (a == b);
    assign a_lt_b = ($signed(a) < $signed(b));
endmodule