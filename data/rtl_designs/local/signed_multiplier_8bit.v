module signed_multiplier_8bit (
    input  signed [7:0] a, b,
    output signed [15:0] product
);
    assign product = a * b;
endmodule