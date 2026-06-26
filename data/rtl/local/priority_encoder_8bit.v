module priority_encoder_8bit (
    input  [7:0] req,
    output reg [2:0] grant,
    output           valid
);
    assign valid = |req;
    always @(*) begin
        casez (req)
            8'b???????1: grant = 3'd0;
            8'b??????10: grant = 3'd1;
            8'b?????100: grant = 3'd2;
            8'b????1000: grant = 3'd3;
            8'b???10000: grant = 3'd4;
            8'b??100000: grant = 3'd5;
            8'b?1000000: grant = 3'd6;
            8'b10000000: grant = 3'd7;
            default:     grant = 3'd0;
        endcase
    end
endmodule