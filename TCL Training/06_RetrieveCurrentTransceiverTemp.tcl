# Simple MIIAE demo for CMIS5 module on 1/1/3

# --- User params ----------------------------------------------------------
set ixOSVersion "10.80.8001.21"
set chassisIp   "10.89.83.99"
set userName    "user"
set port        {1 1 3}   ;# chassis 1, card 1, port 3
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

    puts [format "Reading page 0x%02X (device %d, base 0x%02X) on %d/%d/%d" \
                  $page $deviceNum $base_addr $chasId $cardId $portId]

    miiae presetPage            $page
    miiae presetDeviceNumber    $deviceNum
    miiae presetBaseRegister    $base_addr
    miiae presetNumberOfRegisters 128

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

# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

# Connect / login
ixConnectToChassis $chassisIp
ixLogin $userName

# Show basic transceiver info
scan $port {%d %d %d} chas card prt
puts "Transceiver on port {$port}:"
transceiver get $chas $card $prt
puts "  Vendor       : [transceiver cget -manufacturer]"
puts "  Part Number  : [transceiver cget -model]"
puts "  Serial       : [transceiver cget -serialNumber]"
set revCompliance [transceiver getValue revComplianceProperty]
puts "  RevCompliance: $revCompliance"
puts ""

# --- 1) Test getDeviceNum directly ---------------------------------------
set page 0x00
set base 0x00
set dev [getDeviceNum $page $base]
puts [format "Test getDeviceNum: page 0x%02X, base 0x%02X -> device %d" \
              $page $base $dev]
puts ""

# --- 2) Test readTxcvrPage (lower page 0x00) ------------------------------
if {[readTxcvrPage $port $page $base] != 0} {
    puts "Failed to read page 0x00 – aborting."
    ixLogout
    ixDisconnectAllChassis
    exit 1
}

# --- 3) Test accessTxcvrReg: dump first few bytes -------------------------
puts "First 10 bytes of lower page 0x00:"
foreach a {0 1 2 3 4 5 6 7 8 9} {
    accessTxcvrReg $a
}
puts ""

# --- 4) Decode module temperature (bytes 14–15, CMIS spec) ----------------
set msb [accessTxcvrReg 14 0]
set lsb [accessTxcvrReg 15 0]
set raw [expr {($msb << 8) | $lsb}]

# Signed 16-bit
if {$raw & 0x8000} {
    set raw [expr {$raw - 0x10000}]
}
set tempC [expr {double($raw) / 256.0}]

puts [format "Module temperature = %.2f C (raw 0x%04X)" \
              $tempC [expr {($msb << 8) | $lsb}]]

# Cleanup
ixLogout
puts "Done."
