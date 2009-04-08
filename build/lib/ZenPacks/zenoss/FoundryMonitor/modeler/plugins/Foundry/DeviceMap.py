from Products.DataCollector.plugins.CollectorPlugin import SnmpPlugin, GetMap

class DeviceMap(SnmpPlugin):
    """Map mib elements from Foundry devices mib to get hw and os products.
    """

    maptype = "DeviceMap" 

    snmpGetMap = GetMap({ 
        '.1.3.6.1.4.1.1991.1.1.2.2.1.1.2.1' : 'setHWProductKey',
        '.1.3.6.1.4.1.1991.1.1.1.1.2.0' : 'setHWSerialNumber'
         })
   
    def condition(self, device, log):
        """
        Default condition for portscan is True.
        """
        self.mylog("condition executed")
        return True

    def mylog(self, msg):
        mf = open("/Users/simon/mylog.log", "a")
        mf.write("%s\n" % msg)
        mf.close()

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results
        self.mylog(getdata)
        if getdata['setHWProductKey'] is None: return None
        om = self.objectMap(getdata)
        return om
