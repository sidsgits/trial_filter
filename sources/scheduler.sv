`timescale 1ns/1ps

module scheduler(

    input  logic        clk,
    input  logic        rst_n,

    input  logic [4:0]  valid,
    input  logic [7:0]  data_in [4:0],

    output logic        out_valid,
    output logic [7:0]  out_data,
    output logic [2:0]  out_channel,

    input  logic        out_ready
);

// Implementation goes here

endmodule