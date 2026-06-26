module module_a (input a, b, c, output reg out);
  always @(*) begin
    out = a & b | c;
  end
endmodule