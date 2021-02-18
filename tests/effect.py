from ctypes import *

SUCCESS = 0
ERR_INSTANCE_INVALID = -1
ERR_INSTANCE_ALREADY_EXISTS = -2
ERR_INSTANCE_NON_EXISTS = -3
ERR_INSTANCE_UNLICENSED = -4

ERR_LV2_INVALID_URI = -101
ERR_LV2_INSTANTIATION = -102
ERR_LV2_INVALID_PARAM_SYMBOL = -103
ERR_LV2_INVALID_PRESET_URI = -104
ERR_LV2_CANT_LOAD_STATE = -105

ERR_JACK_CLIENT_CREATION = -201
ERR_JACK_CLIENT_ACTIVATION = -202
ERR_JACK_CLIENT_DEACTIVATION = -203
ERR_JACK_PORT_REGISTER = -204
ERR_JACK_PORT_CONNECTION = -205
ERR_JACK_PORT_DISCONNECTION = -206
ERR_JACK_VALUE_OUT_OF_RANGE = -207

ERR_ASSIGNMENT_ALREADY_EXISTS = -301
ERR_ASSIGNMENT_INVALID_OP = -302
ERR_ASSIGNMENT_LIST_FULL = -303
ERR_ASSIGNMENT_FAILED = -304

ERR_CONTROL_CHAIN_UNAVAILABLE = -401
ERR_ABLETON_LINK_UNAVAILABLE = -402

ERR_MEMORY_ALLOCATION = -901
ERR_INVALID_OPERATION = -902

# Architecture (32-/64-bit) must match your Python version
_fl = CDLL('./mod-host.so')


def cfunc(name, result, *args):
    """Build and apply a ctypes prototype complete with parameter flags"""
    if hasattr(_fl, name):
        atypes = []
        aflags = []
        for arg in args:
            atypes.append(arg[1])
            aflags.append((arg[2], arg[0]) + arg[3:])
        return CFUNCTYPE(result, *atypes)((name, _fl), tuple(aflags))
    else:
        return None


# Bump this up when changing the interface for users
api_version = '1.0.0'

effects_init = cfunc('effects_init', c_int, ('client', c_void_p, 1))

effects_finish = cfunc('effects_finish', c_int, ('close_client', c_int, 1))

effects_add = cfunc('effects_add', c_int,
                    ('uri', c_char_p, 1), ('instance', c_int, 1))

effects_remove = cfunc('effects_remove', c_int, ('effect_id', c_int, 1))

effects_preset_load = cfunc('effects_preset_load', c_int,
                            ('effect_id', c_int, 1), ('uri', c_char_p, 1))

effects_preset_save = cfunc('effects_preset_save', c_int, ('effect_id', c_int, 1),
                            ('dir', c_char_p, 1), ('file_name', c_char_p, 1), ('label', c_char_p, 1))

effects_preset_show = cfunc('effects_preset_show', c_int,
                            ('uri', c_char_p, 1), ('state_str', POINTER(c_char_p), 1))

effects_connect = cfunc('effects_connect', c_int,
                        ('portA', c_char_p, 1), ('portB', c_char_p, 1))

effects_disconnect = cfunc('effects_disconnect', c_int,
                           ('portA', c_char_p, 1), ('portB', c_char_p, 1))

effects_set_parameter = cfunc('effects_set_parameter', c_int, (
    'effect_id', c_int, 1), ('control_symbol', c_char_p, 1), ('value', c_float, 1))

effects_get_parameter = cfunc('effects_get_parameter', c_int, (
    'effect_id', c_int, 1), ('control_symbol', c_char_p, 1), ('value', POINTER(c_float), 1))

effects_set_property = cfunc('effects_set_property', c_int, (
    'effect_id', c_int, 1), ('uri', c_char_p, 1), ('value', c_char_p, 1))

effects_get_property = cfunc(
    'effects_get_property', c_int, ('effect_id', c_int, 1), ('uri', c_char_p, 1))

effects_monitor_parameter = cfunc('effects_monitor_parameter', c_int, (
    'effect_id', c_int, 1), ('control_symbol', c_char_p, 1), ('value', c_float, 1))

effects_monitor_output_parameter = cfunc(
    'effects_monitor_output_parameter', c_int, ('effect_id', c_int, 1), ('control_symbol', c_char_p, 1))

effects_bypass = cfunc('effects_bypass', c_int,
                       ('effect_id', c_int, 1), ('value', c_int, 1))

effects_get_parameter_symbols = cfunc('effects_get_parameter_symbols', c_int, (
    'effect_id', c_int, 1), ('output_ports', c_int, 1), ('symbols', POINTER(c_char_p), 1))

effects_get_presets_uris = cfunc(
    'effects_get_presets_uris', c_int, ('effect_id', c_int, 1), ('uris', POINTER(c_char_p), 1))

effects_get_parameter_info = cfunc('effects_get_parameter_info', c_int, ('effect_id', c_int, 1), (
    'control_symbol', c_char_p, 1), ('range', POINTER(c_float), 1), ('scale_points', POINTER(c_char_p), 1))


class Effect:
    def __init__(self):
        ret = effects_init(None)
        if ret != SUCCESS:
            raise Exception('effects init failed!')
        self.count = 0
        self.effects = {}

    def finish(self):
        effects_finish(1)

    def add(self, name, uri):
        if name in self.effects:
            print(f'effect {name} already added!')
        ret = effects_add(uri.encode(), self.count)
        if ret < SUCCESS:
            print(f'Warn: add effects {uri} failed!')
            return
        self.effects[name] = self.count
        self.count += 1

    def remove(self, name):
        if name not in self.effects:
            print(f'effect {name} not found!')
            return
        idx = self.effects[name]
        effects_remove(idx)

    def index(self, name):
        if name not in self.effects:
            print(f'effect {name} not found!')
            return
        return self.effects[name]

    def get_param(self, name, control_symbol):
        if name not in self.effects:
            print(f'effect {name} not found!')
            return
        idx = self.effects[name]
        val = c_float()
        ret = effects_get_parameter(idx, control_symbol.encode(), byref(val))
        if ret != SUCCESS:
            print(f'get param {control_symbol} failed!')
            return None
        return val.value

    def set_param(self, name, control_symbol, value):
        if name not in self.effects:
            print(f'effect {name} not found!')
            return
        idx = self.effects[name]
        val = c_float(value)
        ret = effects_set_parameter(idx, control_symbol.encode(), val)
        if ret != SUCCESS:
            print(f'set param {control_symbol} failed!')

    def param_symbols(self, name):
        if name not in self.effects:
            print(f'effect {name} not found!')
            return
        idx = self.effects[name]
        val = (c_char_p * 128)()
        effects_get_parameter_symbols(idx, 0, val)
        syms = []
        for v in val:
            if v:
                syms.append(v.decode())
        return syms

    def connect(self, port_a, port_b):
        effects_connect(port_a.encode(), port_b.encode())

    def disconnect(self, port_a, port_b):
        effects_disconnect(port_a.encode(), port_b.encode())


if __name__ == '__main__':
    import time
    #uri = 'http://calf.sourceforge.net/plugins/Compressor'
    uri = 'http://calf.sourceforge.net/plugins/Organ'
    fx = Effect()
    n = 'demo'
    fx.add(n, uri)
    syms = fx.param_symbols(n)
    print(syms)
    fx.connect('system:capture_1', 'effect_0:in_l')
    fx.connect('system:capture_2', 'effect_0:in_r')

    time.sleep(3)
    fx.finish()
