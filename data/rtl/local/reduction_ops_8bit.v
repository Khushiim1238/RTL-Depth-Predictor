module reduction_ops_8bit (
    input  [7:0] data,
    output       and_reduce, or_reduce, xor_reduce, nand_reduce, nor_reduce
);
    assign and_reduce  = &data;
    assign or_reduce   = |data;
    assign xor_reduce  = ^data;
    assign nand_reduce = ~(&data);
    assign nor_reduce  = ~(|data);
endmodule