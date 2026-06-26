module subtractor_8bit (
    input  [7:0] a, b,
    input        bin,
    output [7:0] diff,
    output       bout
);
    assign {bout, diff} = a - b - bin;
endmodule