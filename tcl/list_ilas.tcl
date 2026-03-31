# list_ilas.tcl
# Lists all ILA cores and their probes from a connected device.
# Usage: vivado -mode tcl -source list_ilas.tcl -tclargs <hw_server_url> <ltx_file>
#   hw_server_url: e.g. localhost:3121
#   ltx_file:      path to debug_nets.ltx (or "none" to skip probe loading)

set hw_server_url [lindex $argv 0]
set ltx_file      [lindex $argv 1]

if {$hw_server_url eq ""} { set hw_server_url "localhost:3121" }

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

    # Load probe file if provided
    if {$ltx_file ne "none" && $ltx_file ne ""} {
        set_property PROBES.FILE $ltx_file $dev
    }
    refresh_hw_device $dev -quiet

    set ilas [get_hw_ilas -quiet]
    if {[llength $ilas] == 0} {
        puts "FPGA_CLAUDE:JSON:\{\"device\": \"[get_property NAME $dev]\", \"ilas\": \[\]\}"
        close_hw
        exit 0
    }

    # Build single-line JSON (parser reads line-by-line)
    set ila_parts {}
    foreach ila $ilas {
        set ila_name [get_property NAME $ila]
        set depth    [get_property CONTROL.DATA_DEPTH $ila]

        set probes [get_hw_probes -of_objects $ila -quiet]
        set probe_list {}
        foreach probe $probes {
            set pname [get_property NAME $probe]
            set width [get_property WIDTH $probe]
            lappend probe_list "\{\"name\": \"$pname\", \"width\": $width\}"
        }

        lappend ila_parts "\{\"name\": \"$ila_name\", \"depth\": $depth, \"probes\": \[[join $probe_list ", "]\]\}"
    }

    set json "\{\"device\": \"[get_property NAME $dev]\", \"ilas\": \[[join $ila_parts ", "]\]\}"
    puts "FPGA_CLAUDE:JSON:$json"

    close_hw_target -quiet
    close_hw
    exit 0

} err]} {
    puts "FPGA_CLAUDE:ERROR:$err"
    catch {close_hw}
    exit 1
}
