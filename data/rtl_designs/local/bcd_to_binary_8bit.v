module bcd_to_binary_8bit (
    input  [7:0] bcd,      // two BCD digits: bcd[7:4]=tens, bcd[3:0]=units
    output [6:0] binary
);
    // binary = tens*10 + units
    assign binary = (bcd[7:4] * 4'd10) + bcd[3:0];
endmodule