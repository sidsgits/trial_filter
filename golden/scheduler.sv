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

logic [2:0] current_channel;
logic [2:0] rr_pointer;

integer i;

function automatic [2:0] rr_select(input logic [4:0] v, input logic [2:0] start);
    integer k;
    begin
        rr_select = start;
        for (k = 1; k <= 5; k = k + 1) begin
            if (v[(start + k) % 5]) begin
                rr_select = (start + k) % 5;
                return rr_select;
            end
        end
    end
endfunction


always_ff @(posedge clk or negedge rst_n) begin

    if (!rst_n) begin
        current_channel <= 0;
        rr_pointer <= 0;
    end

    else if (out_ready) begin

        // If current request finished → round robin
        if (!valid[current_channel]) begin
            current_channel <= rr_select(valid, current_channel);
            rr_pointer <= current_channel;
        end

        else begin

            // Check higher-priority requests
            for (i = 0; i < 5; i = i + 1) begin
                if (valid[i] && i < current_channel) begin

                    int delta;
                    delta = current_channel - i;

                    if (delta >= 2) begin
                        current_channel <= i;
                    end

                end
            end

        end

    end

end


always_comb begin
    out_channel = current_channel;
    out_valid   = valid[current_channel];
    out_data    = data_in[current_channel];
end

endmodule