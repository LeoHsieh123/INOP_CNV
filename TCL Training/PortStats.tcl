# ===============================================
#  Multi-Port Ixia Stats Monitor (4 ports)
#  Includes Full FEC + Codewords Bin0~Bin15
# ===============================================

set ixOSVersion "10.80.8001.21"

source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis {10.89.83.99}

chassis get "10.89.83.99"

set chassis 1
set card    1
set ports {17 19 21 23}

# 每欄寬度，決定並排是否對齊
set W 60


# -----------------------------------------------------------
# 取得一個 port 所有欄位，組成 list，每一行對應一個項目
# -----------------------------------------------------------
proc get_port_stats {chassis card port} {

    stat get statAllStats $chassis $card $port

    # Link
    if {[stat cget -link] == 1} {
        set link "Up"
    } else {
        set link "Down"
    }

    # Oversize Good CRC
    set oversize           [stat cget -oversize]
    set oversizeCrc        [stat cget -oversizeAndCrcErrors]
    set oversizeGood       [expr {$oversize - $oversizeCrc}]

    # Build result list
    set L {}

    lappend L "Port $port"
    lappend L "Link State                : $link"
    lappend L "Line Speed                : [stat cget -lineSpeed]"
    lappend L "Frames Sent               : [stat cget -framesSent]"
    lappend L "Frames Received           : [stat cget -framesReceived]"
    lappend L "Bytes Sent                : [stat cget -bytesSent]"
    lappend L "Bytes Received            : [stat cget -bytesReceived]"
    lappend L "Oversize (Good CRC)       : $oversizeGood"
    lappend L "CRC Errors                : [stat cget -fcsErrors]"
    lappend L "Bits Sent                 : [stat cget -bitsSent]"
    lappend L "Bits Received             : [stat cget -bitsReceived]"

    # ---- FEC (ALL preserved) ----
    lappend L "FEC Total Bit Errors      : [stat cget -fecTotalBitErrors]"
    lappend L "FEC Max Symbol Errors     : [stat cget -fecMaxSymbolErrors]"
    lappend L "FEC Corrected Codewords   : [stat cget -fecCorrectedCodewords]"
    lappend L "FEC Uncorrectable CWords  : [stat cget -fecUncorrectableCodewords]"
    lappend L "FEC Total Codewords       : [stat cget -fecTotalCodewords]"
    lappend L "pre-FEC BER               : [stat cget -preFecBer]"
    lappend L "FEC Frame Loss Ratio      : [stat cget -fecFrameLossRatio]"
    lappend L "FEC Status                : [stat cget -fecStatus]"
    lappend L "FEC Transcoding Errors    : [stat cget -fecTranscodingErrors]"
    lappend L "FEC Transcoding Uncorr    : [stat cget -fecTranscodingUncorrectableErrors]"
    lappend L "FEC Uncorr Events         : [stat cget -fecUncorrectableSubrowCount]"

    # ---- Codewords Bin 0 ~ 15 ----
    for {set n 0} {$n <= 15} {incr n} {
        set val [stat cget -fecMaxSymbolErrorsBin$n]
        lappend L "CW with $n errors          : $val"
    }

    # ---- Corrected Bit/Byte Stats ----
    lappend L "Corrected 1s Count        : [stat cget -fecCorrected1sCount]"
    lappend L "Corrected 0s Count        : [stat cget -fecCorrected0sCount]"
    lappend L "Corrected Bits Count      : [stat cget -fecCorrectedBitsCount]"
    lappend L "Corrected Bytes Count     : [stat cget -fecCorrectedBytesCount]"

    return $L
}


# -----------------------------------------------------------
# Main Display Loop
# -----------------------------------------------------------
while {1} {

    # 收集全部 ports 的資料
    set all {}
    foreach p $ports {
        lappend all [get_port_stats $chassis $card $p]
    }

    set rows [llength [lindex $all 0]]

    puts "\n================================================================================"
    puts "                          Ixia Multi-Port Dashboard"
    puts "================================================================================\n"

    # 並排輸出
    for {set i 0} {$i < $rows} {incr i} {
        set line ""

        foreach stats $all {
            set item [lindex $stats $i]
            append line [format "%-${::W}s" $item]
        }

        puts $line
    }

    flush stdout
    after 1000
}
