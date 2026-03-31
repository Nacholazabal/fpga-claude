# arm_and_capture.tcl
# Arms an ILA trigger, waits for capture, and exports to CSV.
# Usage: vivado -mode tcl -source arm_and_capture.tcl \
#          -tclargs <hw_server_url> <ltx_file> <ila_name> <out_csv> <trigger_mode> <timeout_ms>
#
#   hw_server_url: e.g. localhost:3121
#   ltx_file:      path to debug_nets.ltx
#   ila_name:      e.g. hw_ila_1 (or "auto" to use first ILA found)
#   out_csv:       output CSV file path
#   trigger_mode:  "immediate" or "basic" (basic = use whatever trigger is configured in ILA)
#   timeout_ms:    milliseconds to wait for trigger before giving up (default 30000)

set hw_server_url [lindex $argv 0]
set ltx_file      [lindex $argv 1]
set ila_name      [lindex $argv 2]
set out_csv       [lindex $argv 3]
set trigger_mode  [lindex $argv 4]
set timeout_ms    [lindex $argv 5]

if {$hw_server_url eq ""} { set hw_server_url "localhost:3121" }
if {$trigger_mode  eq ""} { set trigger_mode  "immediate" }
if {$timeout_ms    eq ""} { set timeout_ms    30000 }

set_param general.maxThreads 1

if {[catch {
    open_hw
    connect_hw_server -url $hw_server_url -quiet
    open_hw_target -quiet

    set devices [get_hw_devices]
    if {[llength $devices] == 0} {
        puts "FPGA_CLAUDE:ERROR:No JTAG devices found."
        close_hw
        exit 1
    }

    # Select FPGA device (skip ARM DAP on Zynq)
    set dev ""
    foreach d $devices {
        set part [get_property PART $d]
        if {[string match "xc*" $part]} {
            set dev $d
            break
        }
    }
    if {$dev eq ""} {
        set dev [lindex $devices 0]
    }
    current_hw_device $dev

    # Load probe file
    if {$ltx_file ne "none" && $ltx_file ne ""} {
        set_property PROBES.FILE $ltx_file $dev
    }
    refresh_hw_device $dev -quiet

    # Resolve ILA name
    set all_ilas [get_hw_ilas -quiet]
    if {[llength $all_ilas] == 0} {
        puts "FPGA_CLAUDE:ERROR:No ILA cores found on device. Did you add ILA debug cores to your design?"
        close_hw
        exit 1
    }

    if {$ila_name eq "auto"} {
        set target_ila [lindex $all_ilas 0]
    } else {
        set target_ila [get_hw_ilas $ila_name -quiet]
        if {$target_ila eq ""} {
            puts "FPGA_CLAUDE:ERROR:ILA '$ila_name' not found. Available: [join $all_ilas {, }]"
            close_hw
            exit 1
        }
    }

    set ila_resolved [get_property NAME $target_ila]
    puts "FPGA_CLAUDE:INFO:Using ILA: $ila_resolved"

    # Set trigger mode
    if {$trigger_mode eq "immediate"} {
        # Force immediate trigger by setting all conditions to don't-care (X)
        set probes [get_hw_probes -of_objects $target_ila -filter {IS_TRIGGER == true} -quiet]
        foreach probe $probes {
            set width [get_property WIDTH $probe]
            set_property TRIGGER_COMPARE_VALUE "eq${width}'b[string repeat X $width]" $probe
        }
        set_property CONTROL.TRIGGER_POSITION 0 $target_ila
    }
    # For "basic" mode: use whatever trigger conditions are already set on the ILA

    # Arm the ILA
    puts "FPGA_CLAUDE:INFO:Arming ILA (mode=$trigger_mode)..."
    run_hw_ila $target_ila

    # Wait for trigger with timeout
    set start_ms [clock milliseconds]
    set captured 0
    while {1} {
        set status [get_property STATUS.CORE_STATUS $target_ila]
        if {$status eq "IDLE" || $status eq "FULL"} {
            # IDLE or FULL after run means capture completed
            set captured 1
            break
        }
        set elapsed [expr {[clock milliseconds] - $start_ms}]
        if {$elapsed >= $timeout_ms} {
            puts "FPGA_CLAUDE:ERROR:Timeout waiting for ILA trigger after ${timeout_ms}ms. ILA state: $status"
            puts "FPGA_CLAUDE:INFO:Tip: use --trigger immediate to capture without waiting for a condition."
            # Reset the ILA
            catch {reset_hw_ila $target_ila -quiet}
            close_hw
            exit 1
        }
        after 200
    }

    # Upload and export
    puts "FPGA_CLAUDE:INFO:Trigger captured, uploading data..."
    set ila_data [upload_hw_ila_data $target_ila]

    # Ensure output directory exists
    set out_dir [file dirname $out_csv]
    if {$out_dir ne "." && $out_dir ne ""} {
        file mkdir $out_dir
    }

    write_hw_ila_data -force -csv_file $out_csv $ila_data
    puts "FPGA_CLAUDE:RESULT:$out_csv"

    set sample_count [get_property STATUS.SAMPLE_COUNT $target_ila]
    set depth        [get_property CONTROL.DATA_DEPTH $target_ila]
    puts "FPGA_CLAUDE:INFO:Captured $sample_count samples (depth=$depth)"

    close_hw_target -quiet
    close_hw
    exit 0

} err]} {
    puts "FPGA_CLAUDE:ERROR:$err"
    catch {close_hw}
    exit 1
}
