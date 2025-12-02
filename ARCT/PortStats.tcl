# params
set ixOSVersion "10.80.8001.21"


source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis   {10.89.83.99}


chassis get "10.89.83.99"

set chassis 1
set card    1
set port    17    ;# GUI Port 1/1

while {1} {
	stat get statAllStats $chassis $card $port
	puts "\n===== Port Stats ====="
	if {[stat cget -link] == 1} {
		puts "Link State                      : Link Up"
	} else {
		puts "Link State                      : Link Down"
	}
	puts "Line Speed                      : [stat cget -lineSpeed]"
	puts "Frames Sent                     : [stat cget -framesSent]"
	puts "Frames Received                 : [stat cget -framesReceived]"

	puts "Bytes Sent                      : [stat cget -bytesSent]"
	puts "Bytes Received                  : [stat cget -bytesReceived]"


	set oversize            [stat cget -oversize]
	set oversizeCrcErrors   [stat cget -oversizeAndCrcErrors]
	set oversizeGoodCrc [expr {$oversize - $oversizeCrcErrors}]
	puts "Oversize (Good CRC)             : $oversizeGoodCrc"
	puts "CRC Errors                      : [stat cget -fcsErrors]"


	puts "Bits Sent                       : [stat cget -bitsSent]"
	puts "Bits Received                   : [stat cget -bitsReceived]"


	puts "\n===== FEC Statistics ====="

	puts "FEC Total Bit Errors            : [stat cget -fecTotalBitErrors]"
	puts "FEC Max Symbol Errors           : [stat cget -fecMaxSymbolErrors]"
	puts "FEC Corrected Codewords         : [stat cget -fecCorrectedCodewords]"
	puts "FEC Uncorrectable Codewords     : [stat cget -fecUncorrectableCodewords]"
	puts "FEC Total Codewords             : [stat cget -fecTotalCodewords]"
	puts "pre-FEC BER                     : [stat cget -preFecBer]"
	puts "FEC Frame Loss Ratio            : [stat cget -fecFrameLossRatio]"
	puts "FEC Status                      : [stat cget -fecStatus]"
	puts "FEC Transcoding Errors          : [stat cget -fecTranscodingErrors]"
	puts "FEC Transcoding Uncorrectable   : [stat cget -fecTranscodingUncorrectableErrors]"
	puts "FEC Uncorrectable Events        : [stat cget -fecUncorrectableSubrowCount]"

	puts "\n===== FEC Codewords with N Errors ====="
	for {set n 0} {$n <= 15} {incr n} {
		puts "Codewords with $n errors : [stat cget -fecMaxSymbolErrorsBin$n]"
	}

	puts "\n===== FEC Corrected Symbol Stats ====="
	puts "Corrected 1s Count       : [stat cget -fecCorrected1sCount]"
	puts "Corrected 0s Count       : [stat cget -fecCorrected0sCount]"
	puts "Corrected Bits Count     : [stat cget -fecCorrectedBitsCount]"
	puts "Corrected Bytes Count    : [stat cget -fecCorrectedBytesCount]"
    flush stdout

    # 🔁 Refresh interval (1000 ms = 1 second)
    after 1000
}