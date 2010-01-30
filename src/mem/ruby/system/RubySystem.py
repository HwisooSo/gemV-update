from m5.params import *
from m5.SimObject import SimObject

class RubySystem(SimObject):
    type = 'RubySystem'
    random_seed = Param.Int(1234, "random seed used by the simulation");
    randomization = Param.Bool(False,
        "insert random delays on message enqueue times");
    tech_nm = Param.Int(45,
        "device size used to calculate latency and area information");
    clock = Param.Clock('1GHz', "")
    block_size_bytes = Param.Int(64,
        "default cache block size; must be a power of two");
    mem_size_mb = Param.Int("");
    network = Param.RubyNetwork("")
    debug = Param.RubyDebug("the default debug object")
    profiler = Param.RubyProfiler("");
    tracer = Param.RubyTracer("");
    