module min_max_selector_8bit (
    input  [7:0] a, b, c, d,
    output [7:0] minimum, maximum
);
    wire [7:0] min_ab, min_cd, max_ab, max_cd;
    assign min_ab  = (a < b) ? a : b;
    assign min_cd  = (c < d) ? c : d;
    assign minimum = (min_ab < min_cd) ? min_ab : min_cd;
    assign max_ab  = (a > b) ? a : b;
    assign max_cd  = (c > d) ? c : d;
    assign maximum = (max_ab > max_cd) ? max_ab : max_cd;
endmodule