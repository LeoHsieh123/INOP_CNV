# params
set ixOSVersion "10.80.8001.21"


source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis   {10.89.83.99}


chassis get "10.89.83.99"

### Example: Get Chassis Stats
chassis syncChassisStats 1
set chassisStats [chassis getChassisStats 1]
foreach item $chassisStats {
    set value [chassis getChassisStatValue 1 $item]
    puts "$item $value"
}
# all the useful fields you want
set opts {
    -id
    -name
    -serialNumber
    -controllerSerialNumber
    -cableLength
    -sequence
    -master
    -baseIpAddress
    -baseAddressMask
    -syncInOutCountStatus
    -powerConsumption
    -powerManagement
    -inactivityTimeout
    -primary
    -maxCardCount
    -type
    -typeName
    -ipAddress
    -operatingSystem
    -hostName
    -ixServerVersion
    -chassisNumber
    -ip6Address
}

foreach opt $opts {
    set val [chassis cget $opt]
    puts [format "%-25s %s" $opt $val]
}

