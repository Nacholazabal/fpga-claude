# connect_hw.tcl
# Connects to hw_server and returns device info as FPGA_CLAUDE tagged JSON.
# Usage: vivado -mode tcl -source connect_hw.tcl -tclargs <hw_server_url>
#   hw_server_url: e.g. localhost:3121

set hw_server_url [lindex $argv 0]
if {$hw_server_url eq ""} {
    set hw_server_url "localhost:3121"
}

# Suppress Vivado startup banner noise
set_param general.maxThreads 1

if {[catch {
    open_hw
    connect_hw_server -url $hw_server_url -quiet
    open_hw_target -quiet

    set devices [get_hw_devices]
    if {[llength $devices] == 0} {
        puts "FPGA_CLAUDE:ERROR:No JTAG devices found. Check board power and USB connection."
        close_hw
        exit 1
    }

    # Build single-line JSON output (parser reads line-by-line)
    set json_parts {}
    foreach dev $devices {
        set name [get_property NAME $dev]
        set part [get_property PART $dev]
        set ir_len [get_property IR_LENGTH $dev]
        lappend json_parts "\{\"name\": \"$name\", \"part\": \"$part\", \"ir_length\": $ir_len\}"
    }
    set json "\{\"hw_server\": \"$hw_server_url\", \"devices\": \[[join $json_parts ", "]\]\}"
    puts "FPGA_CLAUDE:JSON:$json"

    close_hw_target -quiet
    close_hw
    exit 0

} err]} {
    puts "FPGA_CLAUDE:ERROR:$err"
    catch {close_hw}
    exit 1
}
