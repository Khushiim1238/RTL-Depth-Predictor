module bcd_adder (
    input  [3:0] a, b,
    input        cin,
    output [3:0] sum,
    output       cout
);
    wire [4:0] tmp;
    assign tmp  = a + b + cin;
    assign cout = (tmp > 9) ? 1'b1 : 1'b0;
    assign sum  = (tmp > 9) ? (tmp + 4'd6) : tmp[3:0];
endmodule