# Simple CMIS5 temperature monitor for 1/1/3
#   - samples every 5 seconds
#   - total duration ~60 seconds

# --- User params ----------------------------------------------------------
set ixOSVersion "10.80.8001.21"
set chassisIp   "10.89.83.99"
set userName    "user"
set port        {1 1 3}   ;# chassis 1, card 1, port 3

set durationSec 10        ;# total monitoring time
set intervalMs  2000      ;# 5000 ms = 5 seconds between samples
# -------------------------------------------------------------------------


# Load IxTclHal / IxiaWish bootstrap
source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package require IxTclHal

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

# Only CMIS5 mapping here (simple).
proc getDeviceNum {page addr} {
    set p [expr {$page}]

    switch -- $p {
        0  { return [expr {$addr < 0x80 ? 0 : 1}] }
        1  { return 2 }
        2  { return 3 }
        4  { return 4 }
        16 { return 5 }
        17 { return 6 }
        18 { return 7 }
        19 { return 8 }
        20 { return 9 }
        21 { return 10 }
        default {
            if {$p >= 0x20 && $p <= 0x2F} {
                # VDM 0x20..0x2F -> 11..26
                return [expr {$p - 21}]
            } else {
                return 0
            }
        }
    }
}

# Read one 128-byte block from the module
proc readTxcvrPage {port page base_addr} {
    scan $port {%d %d %d} chasId cardId portId

    set deviceNum [getDeviceNum $page $base_addr]

    miiae presetPage               $page
    miiae presetDeviceNumber       $deviceNum
    miiae presetBaseRegister       $base_addr
    miiae presetNumberOfRegisters  128

    if {[miiae get $chasId $cardId $portId 1]} {
        puts "ERROR: miiae get failed"
        return -1
    }

    miiae getDevice $deviceNum
    return 0
}

# Access one register after readTxcvrPage()
proc accessTxcvrReg {addr {verbose 1}} {
    mmd getRegister $addr
    set regName [mmdRegister cget -name]
    set regVal  [mmdRegister cget -registerValue]

    scan $regVal %x decVal

    if {$verbose} {
        puts [format "  reg %3d (0x%02X) %-40s = 0x%02X (%d)" \
                      $addr $addr $regName $decVal $decVal]
    }
    return $decVal
}

# Get module temperature in °C from CMIS page 0x00 bytes 14–15
proc getModuleTempC {port} {
    set page 0x00
    set base 0x00

    if {[readTxcvrPage $port $page $base] != 0} {
        error "readTxcvrPage failed"
    }

    # CMIS: temperature is a signed 16-bit value at bytes 14–15, units 1/256 °C
    set msb [accessTxcvrReg 14 0]
    set lsb [accessTxcvrReg 15 0]
    set raw [expr {($msb << 8) | $lsb}]

    if {$raw & 0x8000} {
        set raw [expr {$raw - 0x10000}]    ;# sign-extend
    }

    return [expr {double($raw) / 256.0}]
}

# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

# Connect / login
ixConnectToChassis $chassisIp
ixLogin $userName

# Show basic transceiver info once
scan $port {%d %d %d} chas card prt
puts "Transceiver on port {$port}:"
transceiver get $chas $card $prt
puts "  Vendor       : [transceiver cget -manufacturer]"
puts "  Part Number  : [transceiver cget -model]"
puts "  Serial       : [transceiver cget -serialNumber]"
set revCompliance [transceiver getValue revComplianceProperty]
puts "  RevCompliance: $revCompliance"
puts ""

# Monitoring loop
set iterations [expr {int( ($durationSec * 1000) / $intervalMs )}]
puts [format "Monitoring temperature for %d seconds, every %.1f seconds..." \
              $durationSec [expr {$intervalMs/1000.0}]]
puts ""

for {set i 0} {$i < $iterations} {incr i} {
    set now   [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
    set tempC [getModuleTempC $port]

    puts [format "%s : %.2f C" $now $tempC]

    if {$i < $iterations-1} {
        after $intervalMs
    }
}

# Cleanup
ixLogout
puts "Done."
