module carry_lookahead_adder_8bit (
    input  [7:0] a, b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    wire [7:0] g, p;          // generate, propagate
    wire [8:0] c;

    assign g = a & b;
    assign p = a | b;
    assign c[0] = cin;

    // CLA: c[i+1] = g[i] | (p[i] & c[i])
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1)
            assign c[i+1] = g[i] | (p[i] & c[i]);
    endgenerate

    assign sum  = a ^ b ^ c[7:0];
    assign cout = c[8];
endmodule