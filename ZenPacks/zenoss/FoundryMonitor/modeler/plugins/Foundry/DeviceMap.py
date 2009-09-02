##########################################################################
#
#   Copyright 2008, 2009 Zenoss, Inc. All Rights Reserved.
#
##########################################################################

__doc__ = """DeviceMap
Use the Foundry devices MIB to get hw and os products.
"""

from Products.DataCollector.plugins.CollectorPlugin import SnmpPlugin, GetMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, ObjectMap, RelationshipMap


class DeviceMap(SnmpPlugin):
    """Map mib elements from Foundry devices mib to get hw and os products.
    """
    maptype = "DeviceMap" 
    #use these globally for this plugin
    foundryName = "Foundry Inc."
    ironwareName = "IronWare"
   
    #stored in snAgentBrdMainBrdId as the 3rd octet 
    processorMap = {
            3: 'PVR_M603', 
            4: 'PVR_M604', 
            6: 'PVR_M603E',
            7: 'PVR_M603EV',
            8: 'PVR_M750', 
            9: 'PVR_M604E', 
            129: 'PVR_M8245'
        }
    
    snmpGetMap = GetMap({ 
            '.1.3.6.1.4.1.1991.1.1.2.2.1.1.2.1' : 'hwProdKey',
            '.1.3.6.1.4.1.1991.1.1.1.1.2.0' : 'setHWSerialNumber',
            '.1.3.6.1.4.1.1991.1.1.2.1.11.0' : 'firmVer',
            '.1.3.6.1.4.1.1991.1.1.2.1.49.0' : 'firmLabel',
            '.1.3.6.1.4.1.1991.1.1.1.1.13.0' : 'snAgentBrdMainBrdId'
         })
   
    def condition(self, device, log):
        return True

    def hex2int(self, hex):
        mint = "Unknown"
        try:
            mint = int(hex, 16)
        finally:
            return mint

    def getProcessorDetails(self, octetThree, octetFourFive, log):
        """determine the processor type and speed, and build maps"""
        log.info("Processor type: %s, Processor speed: %s" % (octetThree, octetFourFive))
        myp = self.hex2int(octetThree) 
        if self.processorMap.has_key(myp):
            myp = self.processorMap[myp]
        else:
            myp = "Unknown"
            log.error("Problem determining processor type for type %s" % myp)
        mys = self.hex2int(octetFourFive)
        om = ObjectMap( {'id': '0', 'clockspeed': mys, 'extspeed': mys},
                        compname="hw",
                        modname="Products.ZenModel.CPU" )
        om.setProductKey = MultiArgs(myp, self.foundryName)
        rm = RelationshipMap(compname="hw", 
                            relname="cpus", 
                            modname="Products.ZenModel.CPU")
        rm.append(om)
        return rm
       
    def getDRAM(self, octetTenThroughThirteen):
        """get the amount of installed DRAM"""
        myram = self.hex2int(octetTenThroughThirteen)
        if myram == "Unknown":
            myram = 0
        return long(myram * 1024)

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results
        if not getdata['setHWSerialNumber']: return None
        maps = []
        om = self.objectMap(getdata)
        #get processor details and dram 
        if getdata['snAgentBrdMainBrdId']:
            #cheat by using asmac method and then splitting 
            hexar = self.asmac(getdata['snAgentBrdMainBrdId']).split(":")
            proc = self.getProcessorDetails(hexar[3], "".join(hexar[4:6]), log)
            dram = self.getDRAM("".join(hexar[10:14]))
            maps.append(ObjectMap({"totalMemory": dram}, compname="hw"))
            maps.append(proc)
        if getdata['firmVer'] and getdata['firmLabel']:
            om.setOSProductKey = MultiArgs(
                                "%s (%s)" % (getdata['firmVer'], getdata['firmLabel']), 
                                self.ironwareName)
        if getdata['hwProdKey']:
            om.setHWProductKey = MultiArgs(getdata['hwProdKey'], self.foundryName) 
        maps.append(om)
        return maps 
