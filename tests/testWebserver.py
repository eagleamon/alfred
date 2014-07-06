from nose import tools as nt
import alfred

def test_address_in_network():
    check = alfred.handlers.addressInNetwork
    nt.assert_true(check('192.168.1.30', '192.168.1.0/24'))
    nt.assert_false(check('1.2.3.4', '192.158.1.0/24'))
