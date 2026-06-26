module array_multiplier_8bit (
    input  [7:0] a, b,
    output [15:0] product
);
    assign product = a * b;
endmodule