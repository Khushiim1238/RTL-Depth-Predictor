module array_multiplier_16bit (
    input  [15:0] a, b,
    output [31:0] product
);
    assign product = a * b;
endmodule