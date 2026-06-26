module binary_decoder_3to8 (
    input  [2:0] in,
    input        en,
    output [7:0] out
);
    assign out = en ? (8'd1 << in) : 8'd0;
endmodule