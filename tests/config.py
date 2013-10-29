from alfred import config
import json

def testDefault():
    assert config.get('http', 'port') == 8000

def testLoadJson():
    open('testconf.json', 'w').write(json.dumps(dict(http=dict(port=9000, debug=False))))
    config.load(filePath='testconf.json')
    assert config.get('http', 'port') == 9000, config.localConfig
    assert config.get('http', 'debug') == False

# def testLoadYaml():
#     pass