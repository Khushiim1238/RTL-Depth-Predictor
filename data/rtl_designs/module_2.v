module module_b (input a, b, c, d, output reg out);
  always @(*) begin
    out = (a & b) | (c & d);
  end
endmodule