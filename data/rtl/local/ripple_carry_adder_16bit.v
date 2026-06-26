module ripple_carry_adder_16bit (
    input  [15:0] a, b,
    input         cin,
    output [15:0] sum,
    output        cout
);
    assign {cout, sum} = a + b + cin;
endmodule