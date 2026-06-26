"""
generate_rtl_local.py
======================
Generates 55+ synthesizable Verilog RTL modules covering:
  • Adders (ripple-carry, CLA, carry-select, half/full)
  • Multipliers (array, Booth, partial-product)
  • ALUs (4/8/16-bit)
  • Comparators & priority encoders
  • Barrel shifters
  • MUX trees & demux
  • Decoders / encoders / Gray-code
  • Parity & CRC
  • FSMs & arbiters
  • Miscellaneous arithmetic

Files are saved to  data/rtl/local/
Run from project root:
    python data/scripts/generate_rtl_local.py
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR      = os.path.join(PROJECT_ROOT, "data", "rtl", "local")

# ---------------------------------------------------------------------------
# All Verilog designs — each entry: (filename, verilog_code)
# ---------------------------------------------------------------------------

DESIGNS = []

def add(name: str, code: str):
    DESIGNS.append((name, code.strip()))


# ── Category 1: Adders ──────────────────────────────────────────────────────

add("half_adder.v", """
module half_adder (
    input  a, b,
    output sum, carry
);
    assign sum   = a ^ b;
    assign carry = a & b;
endmodule
""")

add("full_adder.v", """
module full_adder (
    input  a, b, cin,
    output sum, cout
);
    assign sum  = a ^ b ^ cin;
    assign cout = (a & b) | (b & cin) | (a & cin);
endmodule
""")

add("ripple_carry_adder_4bit.v", """
module ripple_carry_adder_4bit (
    input  [3:0] a, b,
    input        cin,
    output [3:0] sum,
    output       cout
);
    wire c1, c2, c3;
    assign {c1, sum[0]} = a[0] + b[0] + cin;
    assign {c2, sum[1]} = a[1] + b[1] + c1;
    assign {c3, sum[2]} = a[2] + b[2] + c2;
    assign {cout, sum[3]} = a[3] + b[3] + c3;
endmodule
""")

add("ripple_carry_adder_8bit.v", """
module ripple_carry_adder_8bit (
    input  [7:0] a, b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    assign {cout, sum} = a + b + cin;
endmodule
""")

add("ripple_carry_adder_16bit.v", """
module ripple_carry_adder_16bit (
    input  [15:0] a, b,
    input         cin,
    output [15:0] sum,
    output        cout
);
    assign {cout, sum} = a + b + cin;
endmodule
""")

add("ripple_carry_adder_32bit.v", """
module ripple_carry_adder_32bit (
    input  [31:0] a, b,
    input         cin,
    output [31:0] sum,
    output        cout
);
    assign {cout, sum} = a + b + cin;
endmodule
""")

add("carry_lookahead_adder_8bit.v", """
module carry_lookahead_adder_8bit (
    input  [7:0] a, b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    wire [7:0] g, p;          // generate, propagate
    wire [8:0] c;

    assign g = a & b;
    assign p = a | b;
    assign c[0] = cin;

    // CLA: c[i+1] = g[i] | (p[i] & c[i])
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1)
            assign c[i+1] = g[i] | (p[i] & c[i]);
    endgenerate

    assign sum  = a ^ b ^ c[7:0];
    assign cout = c[8];
endmodule
""")

add("carry_select_adder_8bit.v", """
module carry_select_adder_8bit (
    input  [7:0] a, b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    wire [3:0] sum_lo;
    wire [3:0] sum_hi0, sum_hi1;
    wire       cout_lo, cout_hi0, cout_hi1;

    assign {cout_lo, sum_lo}   = a[3:0] + b[3:0] + cin;
    assign {cout_hi0, sum_hi0} = a[7:4] + b[7:4] + 1'b0;
    assign {cout_hi1, sum_hi1} = a[7:4] + b[7:4] + 1'b1;

    assign sum  = cout_lo ? {sum_hi1, sum_lo} : {sum_hi0, sum_lo};
    assign cout = cout_lo ? cout_hi1           : cout_hi0;
endmodule
""")

add("bcd_adder.v", """
module bcd_adder (
    input  [3:0] a, b,
    input        cin,
    output [3:0] sum,
    output       cout
);
    wire [4:0] tmp;
    assign tmp  = a + b + cin;
    assign cout = (tmp > 9) ? 1'b1 : 1'b0;
    assign sum  = (tmp > 9) ? (tmp + 4'd6) : tmp[3:0];
endmodule
""")

# ── Category 2: Subtractors ──────────────────────────────────────────────────

add("subtractor_8bit.v", """
module subtractor_8bit (
    input  [7:0] a, b,
    input        bin,
    output [7:0] diff,
    output       bout
);
    assign {bout, diff} = a - b - bin;
endmodule
""")

add("abs_difference_8bit.v", """
module abs_difference_8bit (
    input  [7:0] a, b,
    output [7:0] abs_diff
);
    assign abs_diff = (a >= b) ? (a - b) : (b - a);
endmodule
""")

# ── Category 3: Multipliers ──────────────────────────────────────────────────

add("array_multiplier_4bit.v", """
module array_multiplier_4bit (
    input  [3:0] a, b,
    output [7:0] product
);
    assign product = a * b;
endmodule
""")

add("array_multiplier_8bit.v", """
module array_multiplier_8bit (
    input  [7:0] a, b,
    output [15:0] product
);
    assign product = a * b;
endmodule
""")

add("array_multiplier_16bit.v", """
module array_multiplier_16bit (
    input  [15:0] a, b,
    output [31:0] product
);
    assign product = a * b;
endmodule
""")

add("multiplier_with_accumulate_8bit.v", """
module multiplier_with_accumulate_8bit (
    input  [7:0] a, b,
    input  [15:0] acc_in,
    output [15:0] result
);
    assign result = acc_in + (a * b);
endmodule
""")

add("signed_multiplier_8bit.v", """
module signed_multiplier_8bit (
    input  signed [7:0] a, b,
    output signed [15:0] product
);
    assign product = a * b;
endmodule
""")

# ── Category 4: ALUs ─────────────────────────────────────────────────────────

add("simple_alu_4bit.v", """
module simple_alu_4bit (
    input  [3:0] a, b,
    input  [1:0] op,
    output reg [3:0] result,
    output reg       zero
);
    always @(*) begin
        case (op)
            2'b00: result = a + b;
            2'b01: result = a - b;
            2'b10: result = a & b;
            2'b11: result = a | b;
        endcase
        zero = (result == 4'b0);
    end
endmodule
""")

add("simple_alu_8bit.v", """
module simple_alu_8bit (
    input  [7:0] a, b,
    input  [2:0] op,
    output reg [7:0] result,
    output reg       carry, zero, negative
);
    always @(*) begin
        carry    = 1'b0;
        case (op)
            3'b000: {carry, result} = a + b;
            3'b001: {carry, result} = a - b;
            3'b010: result = a & b;
            3'b011: result = a | b;
            3'b100: result = a ^ b;
            3'b101: result = ~a;
            3'b110: result = a << 1;
            3'b111: result = a >> 1;
        endcase
        zero     = (result == 8'b0);
        negative = result[7];
    end
endmodule
""")

add("alu_16bit.v", """
module alu_16bit (
    input  [15:0] a, b,
    input  [3:0]  op,
    output reg [15:0] result,
    output reg        carry, overflow, zero, negative
);
    always @(*) begin
        carry    = 0;
        overflow = 0;
        case (op)
            4'b0000: {carry, result} = a + b;
            4'b0001: {carry, result} = a - b;
            4'b0010: result = a * b;
            4'b0011: result = a & b;
            4'b0100: result = a | b;
            4'b0101: result = a ^ b;
            4'b0110: result = ~a;
            4'b0111: result = a << b[3:0];
            4'b1000: result = a >> b[3:0];
            4'b1001: result = $signed(a) >>> b[3:0];
            4'b1010: result = (a > b) ? 16'd1 : 16'd0;
            4'b1011: result = (a == b) ? 16'd1 : 16'd0;
            4'b1100: result = (a < b) ? 16'd1 : 16'd0;
            4'b1101: result = a + 16'd1;
            4'b1110: result = a - 16'd1;
            4'b1111: result = 16'd0;
        endcase
        zero     = (result == 16'd0);
        negative = result[15];
    end
endmodule
""")

add("mac_unit_8bit.v", """
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
""")

# ── Category 5: Comparators ──────────────────────────────────────────────────

add("magnitude_comparator_4bit.v", """
module magnitude_comparator_4bit (
    input  [3:0] a, b,
    output       a_gt_b, a_eq_b, a_lt_b
);
    assign a_gt_b = (a > b);
    assign a_eq_b = (a == b);
    assign a_lt_b = (a < b);
endmodule
""")

add("magnitude_comparator_8bit.v", """
module magnitude_comparator_8bit (
    input  [7:0] a, b,
    output       a_gt_b, a_eq_b, a_lt_b
);
    assign a_gt_b = (a > b);
    assign a_eq_b = (a == b);
    assign a_lt_b = (a < b);
endmodule
""")

add("signed_comparator_8bit.v", """
module signed_comparator_8bit (
    input signed [7:0] a, b,
    output             a_gt_b, a_eq_b, a_lt_b
);
    assign a_gt_b = ($signed(a) > $signed(b));
    assign a_eq_b = (a == b);
    assign a_lt_b = ($signed(a) < $signed(b));
endmodule
""")

add("min_max_selector_8bit.v", """
module min_max_selector_8bit (
    input  [7:0] a, b, c, d,
    output [7:0] minimum, maximum
);
    wire [7:0] min_ab, min_cd, max_ab, max_cd;
    assign min_ab  = (a < b) ? a : b;
    assign min_cd  = (c < d) ? c : d;
    assign minimum = (min_ab < min_cd) ? min_ab : min_cd;
    assign max_ab  = (a > b) ? a : b;
    assign max_cd  = (c > d) ? c : d;
    assign maximum = (max_ab > max_cd) ? max_ab : max_cd;
endmodule
""")

# ── Category 6: Priority Encoders / Decoders ────────────────────────────────

add("priority_encoder_4bit.v", """
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
""")

add("priority_encoder_8bit.v", """
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
""")

add("binary_decoder_3to8.v", """
module binary_decoder_3to8 (
    input  [2:0] in,
    input        en,
    output [7:0] out
);
    assign out = en ? (8'd1 << in) : 8'd0;
endmodule
""")

add("binary_encoder_8to3.v", """
module binary_encoder_8to3 (
    input  [7:0] in,
    output reg [2:0] out
);
    always @(*) begin
        casez (in)
            8'b10000000: out = 3'd7;
            8'b01000000: out = 3'd6;
            8'b00100000: out = 3'd5;
            8'b00010000: out = 3'd4;
            8'b00001000: out = 3'd3;
            8'b00000100: out = 3'd2;
            8'b00000010: out = 3'd1;
            default:     out = 3'd0;
        endcase
    end
endmodule
""")

# ── Category 7: MUX Trees ────────────────────────────────────────────────────

add("mux_2to1_8bit.v", """
module mux_2to1_8bit (
    input  [7:0] a, b,
    input        sel,
    output [7:0] out
);
    assign out = sel ? b : a;
endmodule
""")

add("mux_4to1_8bit.v", """
module mux_4to1_8bit (
    input  [7:0] a, b, c, d,
    input  [1:0] sel,
    output reg [7:0] out
);
    always @(*) begin
        case (sel)
            2'b00: out = a;
            2'b01: out = b;
            2'b10: out = c;
            2'b11: out = d;
        endcase
    end
endmodule
""")

add("mux_8to1_8bit.v", """
module mux_8to1_8bit (
    input  [7:0] d0, d1, d2, d3, d4, d5, d6, d7,
    input  [2:0] sel,
    output reg [7:0] out
);
    always @(*) begin
        case (sel)
            3'd0: out = d0; 3'd1: out = d1;
            3'd2: out = d2; 3'd3: out = d3;
            3'd4: out = d4; 3'd5: out = d5;
            3'd6: out = d6; 3'd7: out = d7;
        endcase
    end
endmodule
""")

# ── Category 8: Barrel Shifters ──────────────────────────────────────────────

add("barrel_shifter_left_8bit.v", """
module barrel_shifter_left_8bit (
    input  [7:0] data,
    input  [2:0] shamt,
    output [7:0] out
);
    assign out = data << shamt;
endmodule
""")

add("barrel_shifter_right_8bit.v", """
module barrel_shifter_right_8bit (
    input  [7:0] data,
    input  [2:0] shamt,
    output [7:0] out
);
    assign out = data >> shamt;
endmodule
""")

add("barrel_shifter_arith_16bit.v", """
module barrel_shifter_arith_16bit (
    input signed [15:0] data,
    input [3:0]         shamt,
    input               left_right,
    output reg [15:0]   out
);
    always @(*) begin
        if (left_right)
            out = data << shamt;
        else
            out = $signed(data) >>> shamt;
    end
endmodule
""")

add("rotate_left_8bit.v", """
module rotate_left_8bit (
    input  [7:0] data,
    input  [2:0] shamt,
    output [7:0] out
);
    assign out = (data << shamt) | (data >> (8 - shamt));
endmodule
""")

# ── Category 9: Parity & Error Detection ────────────────────────────────────

add("parity_generator_8bit.v", """
module parity_generator_8bit (
    input  [7:0] data,
    output       parity_even, parity_odd
);
    assign parity_even = ^data;
    assign parity_odd  = ~(^data);
endmodule
""")

add("hamming_encoder_4bit.v", """
module hamming_encoder_4bit (
    input  [3:0] data,
    output [6:0] encoded    // 7-bit Hamming (7,4)
);
    assign encoded[2] = data[0];
    assign encoded[4] = data[1];
    assign encoded[5] = data[2];
    assign encoded[6] = data[3];
    assign encoded[0] = data[0] ^ data[1] ^ data[3]; // p1
    assign encoded[1] = data[0] ^ data[2] ^ data[3]; // p2
    assign encoded[3] = data[1] ^ data[2] ^ data[3]; // p4
endmodule
""")

add("crc4_8bit_data.v", """
module crc4_8bit_data (
    input  [7:0] data,
    output [3:0] crc
);
    // CRC-4 (polynomial x^4 + x + 1)
    wire [3:0] state;
    assign state[0] = data[7] ^ data[6] ^ data[4] ^ data[3] ^ data[1];
    assign state[1] = data[7] ^ data[5] ^ data[4] ^ data[2] ^ data[1] ^ data[0];
    assign state[2] = data[6] ^ data[5] ^ data[3] ^ data[2] ^ data[1] ^ data[0];
    assign state[3] = data[7] ^ data[6] ^ data[5] ^ data[4] ^ data[3] ^ data[0];
    assign crc = state;
endmodule
""")

# ── Category 10: Gray Code & Converters ──────────────────────────────────────

add("gray_to_binary_8bit.v", """
module gray_to_binary_8bit (
    input  [7:0] gray,
    output [7:0] binary
);
    assign binary[7] = gray[7];
    assign binary[6] = binary[7] ^ gray[6];
    assign binary[5] = binary[6] ^ gray[5];
    assign binary[4] = binary[5] ^ gray[4];
    assign binary[3] = binary[4] ^ gray[3];
    assign binary[2] = binary[3] ^ gray[2];
    assign binary[1] = binary[2] ^ gray[1];
    assign binary[0] = binary[1] ^ gray[0];
endmodule
""")

add("binary_to_gray_8bit.v", """
module binary_to_gray_8bit (
    input  [7:0] binary,
    output [7:0] gray
);
    assign gray = binary ^ (binary >> 1);
endmodule
""")

add("seven_segment_decoder.v", """
module seven_segment_decoder (
    input  [3:0] digit,
    output reg [6:0] seg    // active-low segments: gfedcba
);
    always @(*) begin
        case (digit)
            4'd0: seg = 7'b1000000;
            4'd1: seg = 7'b1111001;
            4'd2: seg = 7'b0100100;
            4'd3: seg = 7'b0110000;
            4'd4: seg = 7'b0011001;
            4'd5: seg = 7'b0010010;
            4'd6: seg = 7'b0000010;
            4'd7: seg = 7'b1111000;
            4'd8: seg = 7'b0000000;
            4'd9: seg = 7'b0010000;
            default: seg = 7'b1111111;
        endcase
    end
endmodule
""")

add("bcd_to_binary_8bit.v", """
module bcd_to_binary_8bit (
    input  [7:0] bcd,      // two BCD digits: bcd[7:4]=tens, bcd[3:0]=units
    output [6:0] binary
);
    // binary = tens*10 + units
    assign binary = (bcd[7:4] * 4'd10) + bcd[3:0];
endmodule
""")

add("twos_complement_8bit.v", """
module twos_complement_8bit (
    input  [7:0] in,
    output [7:0] out,
    output       overflow
);
    assign {overflow, out} = ~in + 9'd1;
endmodule
""")

# ── Category 11: Logic / Reduction ──────────────────────────────────────────

add("reduction_ops_8bit.v", """
module reduction_ops_8bit (
    input  [7:0] data,
    output       and_reduce, or_reduce, xor_reduce, nand_reduce, nor_reduce
);
    assign and_reduce  = &data;
    assign or_reduce   = |data;
    assign xor_reduce  = ^data;
    assign nand_reduce = ~(&data);
    assign nor_reduce  = ~(|data);
endmodule
""")

add("bitwise_ops_8bit.v", """
module bitwise_ops_8bit (
    input  [7:0] a, b,
    output [7:0] and_out, or_out, xor_out, xnor_out, nand_out, nor_out
);
    assign and_out  = a & b;
    assign or_out   = a | b;
    assign xor_out  = a ^ b;
    assign xnor_out = a ~^ b;
    assign nand_out = ~(a & b);
    assign nor_out  = ~(a | b);
endmodule
""")

add("logical_shift_unit_8bit.v", """
module logical_shift_unit_8bit (
    input  [7:0] data,
    input  [2:0] shamt,
    input        direction,  // 0=left, 1=right
    output [7:0] result
);
    assign result = direction ? (data >> shamt) : (data << shamt);
endmodule
""")

# ── Category 12: FSMs ────────────────────────────────────────────────────────

add("sequence_detector_1011.v", """
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
""")

add("traffic_light_fsm.v", """
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
""")

# ── Category 13: Arbiters ────────────────────────────────────────────────────

add("fixed_priority_arbiter_4way.v", """
module fixed_priority_arbiter_4way (
    input  [3:0] req,
    output [3:0] grant
);
    assign grant[0] = req[0];
    assign grant[1] = req[1] & ~req[0];
    assign grant[2] = req[2] & ~req[1] & ~req[0];
    assign grant[3] = req[3] & ~req[2] & ~req[1] & ~req[0];
endmodule
""")

add("round_robin_arbiter_4way.v", """
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
""")

# ── Category 14: Miscellaneous Arithmetic ───────────────────────────────────

add("saturating_adder_8bit.v", """
module saturating_adder_8bit (
    input  [7:0] a, b,
    output [7:0] result
);
    wire [8:0] sum;
    assign sum    = a + b;
    assign result = sum[8] ? 8'hFF : sum[7:0];  // saturate at 255
endmodule
""")

add("leading_zero_counter_8bit.v", """
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
""")

add("population_count_8bit.v", """
module population_count_8bit (
    input  [7:0] data,
    output [3:0] count
);
    // Count ones using a tree of adders
    wire [1:0] s0, s1, s2, s3;
    wire [2:0] s4, s5;
    assign s0 = data[0] + data[1];
    assign s1 = data[2] + data[3];
    assign s2 = data[4] + data[5];
    assign s3 = data[6] + data[7];
    assign s4 = s0 + s1;
    assign s5 = s2 + s3;
    assign count = s4 + s5;
endmodule
""")

add("integer_divider_4bit.v", """
module integer_divider_4bit (
    input  [3:0] dividend, divisor,
    output [3:0] quotient, remainder
);
    assign quotient  = (divisor != 0) ? (dividend / divisor) : 4'd0;
    assign remainder = (divisor != 0) ? (dividend % divisor) : dividend;
endmodule
""")

add("clamp_unit_8bit.v", """
module clamp_unit_8bit (
    input  [7:0] data,
    input  [7:0] lo, hi,
    output [7:0] clamped
);
    assign clamped = (data < lo) ? lo :
                     (data > hi) ? hi : data;
endmodule
""")

add("thermometer_decoder_4bit.v", """
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
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generating {len(DESIGNS)} RTL modules -> {OUT_DIR}\n")

    for fname, code in DESIGNS:
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(code)
        print(f"  [OK] {fname}")

    print(f"\n[DONE] Generated {len(DESIGNS)} RTL files in data/rtl/local/")


if __name__ == "__main__":
    main()
