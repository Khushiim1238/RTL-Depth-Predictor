module crc4_8bit_data (
    input  [7:0] data,
    output [3:0] crc
);
    // CRC-4 (polynomial x^4 + x + 1)
    wire [3:0] state;
    assign state[0] = data[7] ^ data[6] ^ data[4] ^ data[3] ^ data[1];
    assign state[1] = data[7] ^ data[5] ^ data[4] ^ data[2] ^ data[1] ^ data[0];
    assign state[2] = data[6] ^ data[5] ^ data[3] ^ data[2] ^ data[1] ^ data[0];
    assign state[3] = data[7] ^ data[6] ^ data[5] ^ data[4] ^ data[3] ^ data[0];
    assign crc = state;
endmodule