# hack to modify @profile for non-kernprof use
import builtins
builtins.profile = getattr(builtins, 'profile', lambda x: x)
