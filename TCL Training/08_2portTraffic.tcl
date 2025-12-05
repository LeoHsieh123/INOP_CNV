

# Parameters
set ixOSVersion "10.80.8001.21"
source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis   {10.89.83.99}
chassis get "10.89.83.99"
set chassis	  [chassis cget -id]
set card     1
set portList_ [list [list $chassis $card 1] [list $chassis $card 2]]
# 印出port list: 
puts "portList: $portList_"

# Load port 1 port 2 config

source "0801_Port1Config_0.1.1.tcl"

source "0802_Port2Config_0.1.2.tcl"

# delay
after 1000
# 清除測試數據
ixClearStats portList_

after 1000

# 啟動測試，5秒後停下
ixStartTransmit portList_
after 5000
ixStopTransmit portList_
# delay 給stat counter
after 2000

# 取port 1的數值
# stat get statAllStats chas card port  // 取port 1數據給stat handle
# stat cget // show 出所有stat可以cget的選項
# stat cget -framesSent // 取出傳送偵數的總數
stat get statAllStats 1 1 1
set framesTX1 [stat cget -framesSent]
set framesRX1 [stat cget -framesReceived]

# 取port 2的數值
stat get statAllStats 1 1 2
set framesTX2 [stat cget -framesSent]
set framesRX2 [stat cget -framesReceived]

# 印出數值
puts "P1 Tx : $framesTX1\t\tP2 Tx : $framesTX2"
puts "P1 Rx : $framesRX1\t\tP2 Rx : $framesRX2"


