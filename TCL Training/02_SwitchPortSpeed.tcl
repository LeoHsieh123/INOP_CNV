# params
set ixOSVersion "10.80.8001.21"


source "C:/Program Files (x86)/Ixia/IxOS/$ixOSVersion/TclScripts/bin/IxiaWish.tcl"
package req IxTclHal

ixConnectToChassis   {10.89.83.99}

card get 1 1
# 800G port speed
# resourceGroupEx config -mode 800000

#For PAM4 BERT mode
# resourceGroupEx config -attributes "{bert serdesModePam4}" 
resourceGroupEx get 1 1 1
resourceGroupEx config -mode 800000
resourceGroupEx config -attributes "{bert serdesModePam4}" 
resourceGroupEx set 1 1 1
resourceGroupEx write 1 1 1

resourceGroupEx get 1 1 2
resourceGroupEx config -mode 800000
resourceGroupEx config -attributes "{bert serdesModePam4}" 
resourceGroupEx set 1 1 2
resourceGroupEx write 1 1 2

### Example: Set Port Speed to 200G NRZ BERT

# resourceGroupEx get 1 1 1
# resourceGroupEx config -mode 200000
# resourceGroupEx config -attributes "{bert serdesModeNrz}" 
# resourceGroupEx config -modeName "BERT-NRZ"
# resourceGroupEx set 1 1 1
# resourceGroupEx write 1 1 1
# resourceGroupEx get 1 1 2
# resourceGroupEx config -mode 200000
# resourceGroupEx config -attributes "{bert serdesModeNrz}" 
# resourceGroupEx config -modeName "BERT-NRZ"
# resourceGroupEx set 1 1 2
# resourceGroupEx write 1 1 2


### Example: Set Port Speed to 10G NRZ BERT

# resourceGroupEx get 1 1 1
# resourceGroupEx config -attributes "{bert serdesModeNrz}" 
# resourceGroupEx config -modeName "BERT-10G-NRZ"
# resourceGroupEx set 1 1 1
# resourceGroupEx write 1 1 1
# resourceGroupEx get 1 1 2
# resourceGroupEx config -mode 80000
# resourceGroupEx config -attributes "{bert serdesModeNrz}" 
# resourceGroupEx config -modeName "BERT-10G-NRZ"
# resourceGroupEx set 1 1 2
# resourceGroupEx write 1 1 2