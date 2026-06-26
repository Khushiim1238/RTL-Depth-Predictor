module traffic_light_fsm (
    input      clk, rst,
    input [3:0] timer,
    output reg [1:0] light_ns, light_ew  // 00=red 01=yellow 10=green
);
    parameter RED=2'b00, YELLOW=2'b01, GREEN=2'b10;
    parameter NS_GO=0, NS_YIELD=1, EW_GO=2, EW_YIELD=3;
    reg [1:0] state, next_state;

    always @(posedge clk or posedge rst)
        state <= rst ? NS_GO : next_state;

    always @(*) begin
        case (state)
            NS_GO:    next_state = (timer == 4'd0) ? NS_YIELD : NS_GO;
            NS_YIELD: next_state = (timer == 4'd0) ? EW_GO    : NS_YIELD;
            EW_GO:    next_state = (timer == 4'd0) ? EW_YIELD : EW_GO;
            EW_YIELD: next_state = (timer == 4'd0) ? NS_GO    : EW_YIELD;
            default:  next_state = NS_GO;
        endcase
        case (state)
            NS_GO:    begin light_ns = GREEN;  light_ew = RED;    end
            NS_YIELD: begin light_ns = YELLOW; light_ew = RED;    end
            EW_GO:    begin light_ns = RED;    light_ew = GREEN;  end
            EW_YIELD: begin light_ns = RED;    light_ew = YELLOW; end
            default:  begin light_ns = RED;    light_ew = RED;    end
        endcase
    end
endmodule