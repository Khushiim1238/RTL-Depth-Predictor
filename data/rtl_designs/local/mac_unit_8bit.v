module mac_unit_8bit (
    input  [7:0] a, b,
    input  [15:0] acc,
    input         sub_en,
    output [15:0] result
);
    wire [15:0] product;
    assign product = a * b;
    assign result  = sub_en ? (acc - product) : (acc + product);
endmodule