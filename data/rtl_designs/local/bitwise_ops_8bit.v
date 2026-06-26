module bitwise_ops_8bit (
    input  [7:0] a, b,
    output [7:0] and_out, or_out, xor_out, xnor_out, nand_out, nor_out
);
    assign and_out  = a & b;
    assign or_out   = a | b;
    assign xor_out  = a ^ b;
    assign xnor_out = a ~^ b;
    assign nand_out = ~(a & b);
    assign nor_out  = ~(a | b);
endmodule