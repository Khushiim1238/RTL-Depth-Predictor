module hamming_encoder_4bit (
    input  [3:0] data,
    output [6:0] encoded    // 7-bit Hamming (7,4)
);
    assign encoded[2] = data[0];
    assign encoded[4] = data[1];
    assign encoded[5] = data[2];
    assign encoded[6] = data[3];
    assign encoded[0] = data[0] ^ data[1] ^ data[3]; // p1
    assign encoded[1] = data[0] ^ data[2] ^ data[3]; // p2
    assign encoded[3] = data[1] ^ data[2] ^ data[3]; // p4
endmodule