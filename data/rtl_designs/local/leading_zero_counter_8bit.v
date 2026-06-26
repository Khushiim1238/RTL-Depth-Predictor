module leading_zero_counter_8bit (
    input  [7:0] data,
    output reg [3:0] count
);
    always @(*) begin
        casez (data)
            8'b1???????: count = 4'd0;
            8'b01??????: count = 4'd1;
            8'b001?????: count = 4'd2;
            8'b0001????: count = 4'd3;
            8'b00001???: count = 4'd4;
            8'b000001??: count = 4'd5;
            8'b0000001?: count = 4'd6;
            8'b00000001: count = 4'd7;
            8'b00000000: count = 4'd8;
            default:     count = 4'd0;
        endcase
    end
endmodule