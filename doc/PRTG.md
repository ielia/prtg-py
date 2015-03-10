## Incomplete PRTG RESTful API documentation:
* *`/api/getobjectproperty.htm?id={OBJECT_ID}&name={PROPERTY_NAME}&show=text`*
    Get object property/setting (for propertyname look at the "name" of the INPUT fields while editing an object).
* *`/api/getobjectstatus.htm?id={OBJECT_ID}&name={COLUMN_NAME}&show=text`*
    Get object property/setting (for propertyname look at the "name" of the INPUT fields while editing an object).
    * Response:
    ```
    <?xml version="1.0" encoding="UTF-8" ?>
    <prtg>
      <version>15.1.14.1609+</version>
      <result>True</result>
    </prtg>
    ```
* *`/api/getsensordetails.xml?id={SENSOR_ID}`*
    Get details about a sensor (returns an XML).
    * Response:
    ```
    <?xml version="1.0" encoding="UTF-8"?>
    <sensordata>
      <prtg-version>15.1.14.1609+</prtg-version>
      <name><![CDATA[Probe Health]]></name>
      <sensortype><![CDATA[Probe]]></sensortype>
      <interval><![CDATA[60 s]]></interval>
      <probename><![CDATA[PRTG]]></probename>
      <parentgroupname><![CDATA[PRTG]]></parentgroupname>
      <parentdevicename><![CDATA[Probe.Device.]]></parentdevicename>
      <parentdeviceid><![CDATA[40]]></parentdeviceid>
      <lastvalue><![CDATA[99 %]]></lastvalue>
      <lastmessage><![CDATA[OK]]></lastmessage>
      <favorite><![CDATA[]]></favorite>
      <statustext><![CDATA[Up]]></statustext>
      <statusid><![CDATA[3]]></statusid>
      <lastup><![CDATA[40511.5501967593[20 s ago]]]></lastup>
      <lastdown><![CDATA[40511.5407662153[13 m 55 s ago]]]></lastdown>
      <lastcheck><![CDATA[40511.5501967593[20 s ago]]]></lastcheck>
      <uptime><![CDATA[99.9639%]]></uptime>
      <uptimetime><![CDATA[283 d 14 h]]></uptimetime>
      <downtime><![CDATA[0.0361%]]></downtime>
      <downtimetime><![CDATA[2 h 27 m 31 s]]></downtimetime>
      <updowntotal><![CDATA[283 d 16 h [=63% coverage]]]></updowntotal>
      <updownsince><![CDATA[40059.3436475810[452 d 4 h ago]]]></updownsince>
    </sensordata>
    ```
* *`/api/table.xml?content={TABLENAME}&columns={COMMA_SEPARATED_COLUMN_NAMES}&count={MAX_NUMBER_OF_ITEMS}&start={STARTING_AT}&id&output={OUTPUT_FORMAT}&filter_drel=(today|yesterday|7days|30days|6months|12months)&filter_status={STATUS}&filter_tags={@tag(TAG_NAME)}&filter_{COLUMN_NAME}={@FUNCTION(...)}&sortby={COLUMN_NAME}`*
    Get properties or status of multiple objects.
    * content:
        * channels: List of the channels of a sensor (sensor ID required)
        * devices: List of all devices
        * groups: List of all groups
        * history: Recent configuration changes of an object
        * maps: List of maps
        * messages: List of most recent log entries
        * reports: List of reports
        * sensors: List of all sensors
        * sensortree: A tree-like structure of groups, devices and sensors
        * storedreports: List of most recent PDF reports (report ID reqiured)
        * todos: List of most recent todos
        * values: List of most recent results of a sensor (sensor ID required)
    * columns:
        * channels: name,lastvalue_
        * devices: objid,probe,group,device,host,downsens,partialdownsens,downacksens,upsens,warnsens,pausedsens,unusualsens,undefinedsens
        * groups: objid,probe,group,name,downsens,partialdownsens,downacksens,upsens,warnsens,pausedsens,unusualsens,undefinedsens
        * history: dateonly,timeonly,user,message
        * maps: objid,name
        * messages: objid,datetime,parent,type,name,status,message
        * reports: objid,name,template,period,schedule,email,lastrun,nextrun
        * sensors: objid,probe,group,device,sensor,status,message,lastvalue,priority,favorite
        * sensortree:
        * storedreports: name,datetime,size
        * todos: objid,datetime,name,status,priority,message
        * values: datetime,value_,coverage
    * count: 1-50000
    * ouptut:
        * csv: comma separated output _doesn't seem to be working_
        * html: pure HTML _doesn't seem to be working_
        * json: lightweight javascript object notation _doesn't seem to be working_
        * **xml: most suitable for further processing (recommended)**
        * xmltable: structured like an HTML table (easier to convert into a table) _doesn't seem to be working_
* *`/api/setobjectproperty.htm?id={OBJECT_ID}&name={PROPERTY, e.g.: tags}&value={COMMA_SEPARATED_TAGS}`*
* *`/api/getstatus.(htm|xml)?id=0`*
    Current system status in JSON ("htm") or XML ("xml") format.
* *`/api/sensortypesinuse.json`*
    All currently used sensor types in JSON format.

## Complete PRTG RESTful API documentation
Go to `http://{PRTG_HOST}:{PRTG_PORT}/api.htm?tabid=3`
