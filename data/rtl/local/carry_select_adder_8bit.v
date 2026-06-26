module carry_select_adder_8bit (
    input  [7:0] a, b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    wire [3:0] sum_lo;
    wire [3:0] sum_hi0, sum_hi1;
    wire       cout_lo, cout_hi0, cout_hi1;

    assign {cout_lo, sum_lo}   = a[3:0] + b[3:0] + cin;
    assign {cout_hi0, sum_hi0} = a[7:4] + b[7:4] + 1'b0;
    assign {cout_hi1, sum_hi1} = a[7:4] + b[7:4] + 1'b1;

    assign sum  = cout_lo ? {sum_hi1, sum_lo} : {sum_hi0, sum_lo};
    assign cout = cout_lo ? cout_hi1           : cout_hi0;
endmodule