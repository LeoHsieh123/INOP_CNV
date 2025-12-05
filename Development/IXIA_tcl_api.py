from ixexplorer.api.ixe_api import IxeTclApi

api = IxeTclApi("10.89.83.99")
api.connect()
print(api.send("show chassis status"))
api.disconnect()