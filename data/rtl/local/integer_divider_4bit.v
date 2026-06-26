module integer_divider_4bit (
    input  [3:0] dividend, divisor,
    output [3:0] quotient, remainder
);
    assign quotient  = (divisor != 0) ? (dividend / divisor) : 4'd0;
    assign remainder = (divisor != 0) ? (dividend % divisor) : dividend;
endmodule