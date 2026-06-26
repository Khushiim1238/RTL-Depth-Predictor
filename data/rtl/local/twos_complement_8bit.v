module twos_complement_8bit (
    input  [7:0] in,
    output [7:0] out,
    output       overflow
);
    assign {overflow, out} = ~in + 9'd1;
endmodule