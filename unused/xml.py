rawxml = '''<?xml version="1.0" encoding="UTF-8" ?>
<chat xmlns="http://test.org/net/1.3">
    <event sender="Frank" time="2016-02-03T22:58:19+01:00" />
    <message sender="Karen" time="2016-02-03T22:58:19+01:00">
        <div>
            <span>Hello Frank</span>
        </div>
    </message>
    <message sender="Frank" time="2016-02-03T22:58:39+01:00">
        <div>
            <span>Hi there Karen</span>
        </div>
        <div>
            <span>I'm back from New York</span>
        </div>
    </message>
    <message sender="Karen" time="2016-02-03T22:58:56+01:00">
        <div>
            <span>How are you doing?</span>
            <span>Everything OK?</span>
        </div>
    </message>
</chat>'''

ns = {'msg': "http://test.org/net/1.3"}
xml = ET.fromstring(rawxml)

for msg in xml.findall("msg:message", ns):
    print("Sender: " + msg.get("sender"))
    print("Time: " + msg.get("time"))
    body = ""
    for d in msg.findall("msg:div", ns):
        body = body + ET.tostring(d, encoding="unicode")
    print("Content: " + body)
