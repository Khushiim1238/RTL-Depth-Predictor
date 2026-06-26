module fixed_priority_arbiter_4way (
    input  [3:0] req,
    output [3:0] grant
);
    assign grant[0] = req[0];
    assign grant[1] = req[1] & ~req[0];
    assign grant[2] = req[2] & ~req[1] & ~req[0];
    assign grant[3] = req[3] & ~req[2] & ~req[1] & ~req[0];
endmodule