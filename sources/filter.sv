`timescale 1ns/1ps

module filter(
    input clk,
    input rst_n,
    input [10:0] can_id_in,
    input [63:0] can_data_in,
    input can_valid_in,
    output reg filter_match_out,
    output reg [63:0] data_out
);

endmodule