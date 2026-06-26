module saturating_adder_8bit (
    input  [7:0] a, b,
    output [7:0] result
);
    wire [8:0] sum;
    assign sum    = a + b;
    assign result = sum[8] ? 8'hFF : sum[7:0];  // saturate at 255
endmodule