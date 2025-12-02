# ================================================================
# AresONE – Read transceiver management pages (CMIS / SFF)
#   - Connect to chassis
#   - Detect module MSA (SFF-8472 / SFF-8636 / CMIS3/4/5)
#   - Read one page (0x00) via MIIM/MDIO
#   - Dump bytes 0x80–0xFF (upper half of the page)
# ================================================================

# Parameters
set ixOSVersion "10.80.8001.21"
source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

set userName  user
set hostName  "10.89.83.99"
# chassis / card / port
set port      [list 1 1 3]

# ----------------------------------------------------------------------
# getDeviceNum
#   Map (MSA type, CMIS page, base I2C address) to the internal
#   "device number" used by the miiae/mmd APIs.
# ----------------------------------------------------------------------
proc getDeviceNum {page {msa CMIS5} {addr 0x80}} {
    # normalize page (handles 0x10, 16, etc.)
    set p [expr {$page}]
    set deviceNum 0

    switch -- $msa {
        SFF-8472 {
            # SFF-8472 has two I2C devices: 0xA0 (lower) and 0xA2 (upper).
            # We use page >= 20 as a simple way to select the upper device.
            if {$p >= 20} {
                set deviceNum 0xA2
            } else {
                set deviceNum 0
            }
        }

        SFF-8636 -
        SFF-8436 {
            # QSFP+/QSFP28 memory map
            switch -- $p {
                0  { set deviceNum [expr {$addr < 0x80 ? 0 : 1}] }
                1  { set deviceNum 2 }
                2  { set deviceNum 3 }
                3  { set deviceNum 4 }
                default { set deviceNum 0 }
            }
        }

        CMIS5 {
            # CMIS 5.0/5.1 mapping
            # Pages 0x00-0x14 : standard CMIS
            # Page  0x15      : timing characteristics
            # Pages 0x20-0x2F : VDM
            switch -- $p {
                0   { set deviceNum [expr {$addr < 0x80 ? 0 : 1}] }
                1   { set deviceNum 2 }
                2   { set deviceNum 3 }
                4   { set deviceNum 4 }
                16  { set deviceNum 5 }   ;# 0x10
                17  { set deviceNum 6 }   ;# 0x11
                18  { set deviceNum 7 }   ;# 0x12
                19  { set deviceNum 8 }   ;# 0x13
                20  { set deviceNum 9 }   ;# 0x14
                21  { set deviceNum 10 }  ;# 0x15
                default {
                    if {$p >= 0x20 && $p <= 0x2F} {
                        # VDM pages 0x20..0x2F map to deviceNum 11..26
                        set deviceNum [expr {$p - 21}]
                    } else {
                        set deviceNum 0
                    }
                }
            }
        }

        CMIS4 {
            # CMIS 4.x mapping (almost the same as CMIS5, but VDM mapping differs)
            switch -- $p {
                0   { set deviceNum [expr {$addr < 0x80 ? 0 : 1}] }
                1   { set deviceNum 2 }
                2   { set deviceNum 3 }
                4   { set deviceNum 4 }
                16  { set deviceNum 5 }   ;# 0x10
                17  { set deviceNum 6 }   ;# 0x11
                18  { set deviceNum 7 }   ;# 0x12
                19  { set deviceNum 8 }   ;# 0x13
                20  { set deviceNum 9 }   ;# 0x14
                default {
                    if {$p >= 0x20 && $p <= 0x2F} {
                        # VDM pages 0x20..0x2F map to deviceNum 10..25
                        set deviceNum [expr {$p - 22}]
                    } else {
                        set deviceNum 0
                    }
                }
            }
        }

        default {
            # CMIS3 or earlier CMIS flavour
            switch -- $p {
                0   { set deviceNum [expr {$addr < 0x80 ? 0 : 1}] }
                1   { set deviceNum 2 }
                2   { set deviceNum 3 }
                16  { set deviceNum 5 }   ;# 0x10
                17  { set deviceNum 6 }   ;# 0x11
                default { set deviceNum 0 }
            }
        }
    }

    return $deviceNum
}

# ----------------------------------------------------------------------
# readTxcvrPage
#   Read one CMIS/SFF page (128 bytes) into the mmd/miiae buffers
# ----------------------------------------------------------------------
proc readTxcvrPage {port page {msa CMIS5} {addr 0x80} {mdioIndex 1}} {
    scan $port {%d %d %d} chasId cardId portId

    # Resolve "device number" for this (MSA, page, base addr) tuple
    set deviceNum [getDeviceNum $page $msa $addr]

    # Configure register access: start address and how many bytes
    miiae presetPage              $page
    miiae presetDeviceNumber      $deviceNum
    miiae presetBaseRegister      $addr
    miiae presetNumberOfRegisters 128

    # Perform read through the AresONE MIIM/MDIO engine
    if {[miiae get $chasId $cardId $portId $mdioIndex]} {
        errorMsg [format "ERROR - Could not read transceiver management on port {%s}" $port]
        return -1
    }

    # Make sure the device context is selected for subsequent mmd commands
    miiae getDevice $deviceNum
    return 0
}

# ----------------------------------------------------------------------
# accessTxcvrReg
#   Read a single byte from the buffer previously filled by readTxcvrPage
# ----------------------------------------------------------------------
proc accessTxcvrReg {port addr {page 0} {options verbose}} {
    scan $port {%d %d %d} chasId cardId portId

    # (assumes a call to readTxcvrPage has already been done)
    mmd getRegister $addr

    # Name & value come from the "current" mmdRegister object
    set regName [mmdRegister cget -name]
    set regVal  [mmdRegister cget -registerValue]

    # regVal is hex string, convert to integer
    scan $regVal %x decVal

    if {$options eq "verbose"} {
        puts [format "Page 0x%02X, reg %3d (0x%02X) - %-60s => 0x%02X" \
                  $page $addr $addr $regName $decVal]
    }

    return $decVal
}

# ======================================================================
# Main script
# ======================================================================

ixConnectToChassis $hostName
ixLogin $userName

# Display basic transceiver info
scan $port {%d %d %d} chasId cardId portId
puts [format "Transceiver properties of port {%s}:" $port]

transceiver get $chasId $cardId $portId
puts [format "  Vendor Name     : %s" [transceiver cget -manufacturer]]
puts [format "  Part Number     : %s" [transceiver cget -model]]
puts [format "  Serial Number   : %s" [transceiver cget -serialNumber]]
puts [format "  Transceiver Type: %s" [transceiver getValue transceiverTypeProperty]]

# Decode MSA information from transceiver's RevCompliance
set msaRev  0.0
set msaType "Unknown"
set revCompliance [transceiver getValue revComplianceProperty]

if {[llength [split $revCompliance " "]] > 1} {
    set revComplianceList [split [lindex $revCompliance 0] " "]
    set msaType [lindex $revComplianceList 0]
    set msaRev  [lindex $revComplianceList 1]
}

puts [format "  Rev Compliance  : %s" $revCompliance]
puts [format "  MSA Type        : %s" $msaType]
puts [format "  MSA Rev         : %s\n" $msaRev]

# Decide which MSA mapping to use
set msaName "CMIS3"
switch -- $msaType {
    SFF-8472 {
        set msaName "SFF-8472"
    }
    SFF-8636 {
        set msaName "SFF-8636"
    }
    CMIS {
        switch -- $msaRev {
            4.1 -
            5.0 -
            5.1 {
                set msaName "CMIS5"
            }
            4.0 {
                set msaName "CMIS4"
            }
            default {
                set msaName "CMIS3"
            }
        }
    }
}

# ----------------------------------------------------------------------
# Read one transceiver management page and dump bytes 0x80-0xFF
# ----------------------------------------------------------------------
set page       0x00
set base_addr  0

puts "Reading $msaName page $page of port {$port}..."
if {[readTxcvrPage $port $page $msaName $base_addr] != 0} {
    errorMsg "Read failed, aborting."
    return
}

# Now display the register values from the page that has been read
set addr_start 0
set addr_end   128

for {set addr $addr_start} {$addr <= $addr_end} {incr addr} {
    set reg_val [accessTxcvrReg $port $addr $page verbose]
}
