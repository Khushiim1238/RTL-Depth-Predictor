module round_robin_arbiter_4way (
    input      clk, rst,
    input  [3:0] req,
    output reg [3:0] grant
);
    reg [1:0] priority_ptr;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            grant        <= 4'b0;
            priority_ptr <= 2'd0;
        end else begin
            case (priority_ptr)
                2'd0: begin
                    if      (req[0]) begin grant <= 4'b0001; priority_ptr <= 2'd1; end
                    else if (req[1]) begin grant <= 4'b0010; priority_ptr <= 2'd2; end
                    else if (req[2]) begin grant <= 4'b0100; priority_ptr <= 2'd3; end
                    else if (req[3]) begin grant <= 4'b1000; priority_ptr <= 2'd0; end
                    else              grant <= 4'b0;
                end
                2'd1: begin
                    if      (req[1]) begin grant <= 4'b0010; priority_ptr <= 2'd2; end
                    else if (req[2]) begin grant <= 4'b0100; priority_ptr <= 2'd3; end
                    else if (req[3]) begin grant <= 4'b1000; priority_ptr <= 2'd0; end
                    else if (req[0]) begin grant <= 4'b0001; priority_ptr <= 2'd1; end
                    else              grant <= 4'b0;
                end
                default: grant <= 4'b0;
            endcase
        end
    end
endmodule