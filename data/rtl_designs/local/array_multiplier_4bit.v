module array_multiplier_4bit (
    input  [3:0] a, b,
    output [7:0] product
);
    assign product = a * b;
endmodule