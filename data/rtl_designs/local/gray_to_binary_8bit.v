module gray_to_binary_8bit (
    input  [7:0] gray,
    output [7:0] binary
);
    assign binary[7] = gray[7];
    assign binary[6] = binary[7] ^ gray[6];
    assign binary[5] = binary[6] ^ gray[5];
    assign binary[4] = binary[5] ^ gray[4];
    assign binary[3] = binary[4] ^ gray[3];
    assign binary[2] = binary[3] ^ gray[2];
    assign binary[1] = binary[2] ^ gray[1];
    assign binary[0] = binary[1] ^ gray[0];
endmodule