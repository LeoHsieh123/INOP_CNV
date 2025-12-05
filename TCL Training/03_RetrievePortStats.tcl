set ixOSVersion "10.80.8001.21"


source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis   {10.89.83.99}


### Example: Retrieve Port Stats
### 1. stat get statAllStats $chassisId $cardId $portId
### 2. stat cget -stat_you_want

stat get statAllStats 1 1 17
puts "Bert Bits Sent on Port 1: [stat cget -bertBitsSent]"
puts "Bert Bits Receive on Port 1: [stat cget -bertBitsReceived]"


### Example: Retrieve Bert Lanes Stats
### 1. stat getBertLane $chassisId $cardId $portId $laneId
### 2. stat cget -bertLaneStat_you_want
### 3. clear bert lane stats (can only clear all) : stat clearBertLane $chassisId $cardId $portId

stat getBertLane 1 1 17 1
puts "\n"
puts "Port 1 Lane 1 BERT Stats:" 
puts "\tLane|\tBertbitSent\tBertBitsReceived\tBertBitErrRcv\tBertBitErrRcvRatio"
puts "\t|\t\t[stat cget -bertBitsSent]\t[stat cget -bertBitsReceived]\t\t[stat cget -bertBitErrorsReceived]\t\t[stat cget -bertBitErrorRatio]"


