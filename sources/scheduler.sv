`timescale 1ns/1ps

module scheduler(

    input clk,
    input rst_n,

    input  [4:0] valid,
    input  [7:0] data_in [0:4],

    output reg        out_valid,
    output reg [7:0]  out_data,
    output reg [2:0]  out_channel,

    input out_ready
);

reg [2:0] current_channel;
reg [2:0] next_channel;

integer i;
integer k;



/* -------------------------
   Round robin helper
--------------------------*/
function [2:0] rr_select;
    input [4:0] v;
    input [2:0] start;
    begin
        rr_select = start;

        for(k=1;k<=5;k=k+1)
        begin
            if(v[(start+k)%5])
            begin
                rr_select = (start+k)%5;
                k = 6;
            end
        end
    end
endfunction



/* -------------------------
   Next state logic
--------------------------*/
always @(*) begin

    next_channel = current_channel;

    /* higher priority check */
    for(i=0;i<current_channel;i=i+1)
    begin
        if(valid[i] && (current_channel-i>=2))
            next_channel = i;
    end

    /* round robin if current invalid */
    if(!valid[current_channel])
        next_channel = rr_select(valid,current_channel);

end



/* -------------------------
   State register
--------------------------*/
always @(posedge clk or negedge rst_n)
begin

    if(!rst_n)
        current_channel <= 0;

    else if(out_ready)
        current_channel <= next_channel;

end



/* -------------------------
   Output logic
--------------------------*/
always @(*) begin

    /* hold current channel */
    out_channel = current_channel;

    if(valid[current_channel])
    begin
        out_valid = 1;
        out_data  = data_in[current_channel];
    end
    else
    begin
        /* select next valid if current disappears */
        out_channel = rr_select(valid,current_channel);
        out_valid   = valid[out_channel];
        out_data    = data_in[out_channel];
    end

end

endmodule