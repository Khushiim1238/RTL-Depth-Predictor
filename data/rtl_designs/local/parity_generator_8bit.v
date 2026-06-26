module parity_generator_8bit (
    input  [7:0] data,
    output       parity_even, parity_odd
);
    assign parity_even = ^data;
    assign parity_odd  = ~(^data);
endmodule