module population_count_8bit (
    input  [7:0] data,
    output [3:0] count
);
    // Count ones using a tree of adders
    wire [1:0] s0, s1, s2, s3;
    wire [2:0] s4, s5;
    assign s0 = data[0] + data[1];
    assign s1 = data[2] + data[3];
    assign s2 = data[4] + data[5];
    assign s3 = data[6] + data[7];
    assign s4 = s0 + s1;
    assign s5 = s2 + s3;
    assign count = s4 + s5;
endmodule