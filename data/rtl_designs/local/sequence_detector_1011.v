module sequence_detector_1011 (
    input      clk, rst, din,
    output reg detected
);
    parameter S0=0, S1=1, S2=2, S3=3, S4=4;
    reg [2:0] state, next_state;

    always @(posedge clk or posedge rst)
        state <= rst ? S0 : next_state;

    always @(*) begin
        case (state)
            S0: next_state = din ? S1 : S0;
            S1: next_state = din ? S1 : S2;
            S2: next_state = din ? S3 : S0;
            S3: next_state = din ? S4 : S2;
            S4: next_state = din ? S1 : S0;
            default: next_state = S0;
        endcase
        detected = (state == S4);
    end
endmodule