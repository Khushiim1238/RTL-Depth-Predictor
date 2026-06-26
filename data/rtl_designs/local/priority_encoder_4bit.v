module priority_encoder_4bit (
    input  [3:0] req,
    output reg [1:0] grant,
    output       valid
);
    assign valid = |req;
    always @(*) begin
        casez (req)
            4'b???1: grant = 2'd0;
            4'b??10: grant = 2'd1;
            4'b?100: grant = 2'd2;
            4'b1000: grant = 2'd3;
            default: grant = 2'd0;
        endcase
    end
endmodule