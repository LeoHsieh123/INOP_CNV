# params
set ixOSVersion "10.80.8001.21"
source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis   {10.89.83.99}


transceiver get 1 1 17
set manufacturer [transceiver cget -manufacturer]
set model [transceiver cget -model]
set serialNumber [transceiver cget -serialNumber]

puts "Traceiver Type : \t[transceiver getTransceiverType 1 1 3]"
## Tranceiver Properties
puts "Transceiver Information for Port 3:"
set propList [transceiver getReadAvailableProps 1 1 17]
foreach element $propList {
 puts "\t\t$element\t[transceiver getValue $element]"
}

puts "\n\n"

## Tranceiver DOM Info
transceiverDOM get 1 1 3
puts "Transceiver DOM Information for Port 3:"
set DOMpropList [transceiverDOM getReadAvailableProps 1 1 17]
foreach element $DOMpropList {
 puts "\t\t$element\t[transceiverDOM getValue $element]"
}

puts "\n\n"
## PCS Lane Statistics
pcsLaneStatistics get 1 1 17
set title [format "%8s\t%5s\t%8s\t%5s\t%5s\t%8s\t%8s\t%8s\t%8s\t%8s\t%8s\t%8s" pcsLane skew 6466Lock laneLock pcsError vlError lostPcs lostVl fecSymCt fecCBs fecSymRt fecCBRt]
ixPuts $title
ixPuts [string repeat "-" [string length $title]]
for {set i 0} {$i<=31} {incr i} {
pcsLaneStatistics getLane $i

set fecRate  [pcsLaneStatistics cget -fecCorrectedBitRate]
set fecRateRounded [format "%.3g" [expr {$fecRate + 0.0}]]

ixPuts [format "%8s\t%5s\t%8s\t%5s\t%5s\t%8s\t%8s\t%8s\t%8s\t%8s\t%8s\t%8s" \
 [pcsLaneStatistics cget -pcsLaneMarkerMap] \
 [pcsLaneStatistics cget -relativeLaneSkew] \
 [pcsLaneStatistics cget -syncHeaderLock] \
 [pcsLaneStatistics cget -pcsLaneMarkerLock] \
 [pcsLaneStatistics cget -pcsLaneMarkerErrorCount] \
 [pcsLaneStatistics cget -bip8ErrorCount] \
 [pcsLaneStatistics cget -lostSyncHeaderLock] \
 [pcsLaneStatistics cget -lostPcsLaneMarkerLock] \
 [pcsLaneStatistics cget -fecSymbolErrorCount] \
 [pcsLaneStatistics cget -fecCorrectedBitsCount] \
 [pcsLaneStatistics cget -fecSymbolErrorRate] \
 $fecRateRounded ]
}