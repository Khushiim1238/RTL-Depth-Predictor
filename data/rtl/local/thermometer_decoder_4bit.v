module thermometer_decoder_4bit (
    input  [3:0] thermo,
    output reg [1:0] binary
);
    always @(*) begin
        casez (thermo)
            4'b1111: binary = 2'd3;
            4'b0111: binary = 2'd2;
            4'b0011: binary = 2'd1;
            4'b0001: binary = 2'd0;
            default: binary = 2'd0;
        endcase
    end
endmodule