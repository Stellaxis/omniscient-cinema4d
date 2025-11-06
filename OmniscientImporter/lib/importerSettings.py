import c4d
from c4d import plugins
from contextlib import contextmanager

@contextmanager
def adjust_scale(extension, scale=1.0, unit=c4d.DOCUMENT_UNIT_M):
    """Temporarily enforce safe importer settings for the given extension."""
    if not isinstance(extension, str):
        yield False
        return

    ext = extension.lower()
    plugin_id = importer_plugin_ids.get(ext)
    if plugin_id is None:
        yield False
        return

    scale_data = c4d.UnitScaleData()
    try:
        scale_data.SetUnitScale(scale, unit)
    except Exception:
        yield False
        return

    if ext == 'abc':
        settings = build_abc_settings(scale_data)
    elif ext == 'obj':
        settings = build_obj_settings(scale_data)
    else:
        settings = None

    if not settings:
        yield False
        return

    with temporary_importer_settings(plugin_id, settings, is_loader=True):
        yield True  # or just `yield` if the caller ignores this value

importer_plugin_ids = {
    # Use modern importer IDs where available; fall back to legacy numeric IDs.
    'obj': getattr(c4d, 'FORMAT_OBJ2IMPORT', 1030177),
    'abc': getattr(c4d, 'FORMAT_ABCIMPORT', 1028081),
}

def get_plugin_by_id(plugin_id, is_loader=False):
    operation = dict()
    plugin_type = c4d.PLUGINTYPE_SCENELOADER if is_loader else c4d.PLUGINTYPE_SCENESAVER
    plugin = plugins.FindPlugin(plugin_id, plugin_type)
    if plugin is None:
        return None
    try:
        if not plugin.Message(c4d.MSG_RETRIEVEPRIVATEDATA, operation):
            return None
    except Exception:
        return None
    return operation.get("imexporter")

# ------------------------------
# Utilities to preserve user prefs
# ------------------------------

def _clone_bc(bc):
    if bc is None:
        return c4d.BaseContainer()
    try:
        return bc.GetClone()
    except TypeError:
        return bc.GetClone(c4d.COPYFLAGS_NONE)

def _get_world_bc(pid):
    bc = plugins.GetWorldPluginData(pid)
    return bc if bc is not None else c4d.BaseContainer()

def _set_world_plugin_data(pid, bc, add_flag=False):
    try:
        plugins.SetWorldPluginData(pid, bc, add=add_flag)
    except TypeError:
        # Older SDKs do not expose the 'add' parameter in Python.
        plugins.SetWorldPluginData(pid, bc)

def _get_plugin_and_imexporter(pid, is_loader=True):
    op = {}
    ptype = c4d.PLUGINTYPE_SCENELOADER if is_loader else c4d.PLUGINTYPE_SCENESAVER
    plug = plugins.FindPlugin(pid, ptype)
    if not plug:
        return None, None
    try:
        if not plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op):
            return plug, None
    except Exception:
        return plug, None
    return plug, op.get("imexporter")

def _apply_to_instance_and_world(pid, kv_pairs, is_loader=True):
    plug, inst = _get_plugin_and_imexporter(pid, is_loader)
    if plug is None or inst is None:
        return False
    world_bc = _get_world_bc(pid)
    for k, v in kv_pairs:
        if k is None:
            continue
        try:
            inst[k] = v
            world_bc[k] = v
        except Exception:
            pass
    _set_world_plugin_data(pid, world_bc, add_flag=True)
    return True

@contextmanager
def temporary_importer_settings(pid, kv_pairs, is_loader=True):
    """Temporarily apply importer settings and restore user prefs afterwards."""
    world_backup = _clone_bc(_get_world_bc(pid))
    _, inst = _get_plugin_and_imexporter(pid, is_loader)
    # Make a copy of the live data container (GetData() is deprecated since 2024)
    try:
        inst_backup = (
            inst.GetDataInstance().GetClone(c4d.COPYFLAGS_NONE)
            if inst is not None else None
        )
    except Exception:
        inst_backup = None
    try:
        _apply_to_instance_and_world(pid, kv_pairs, is_loader=is_loader)
        yield
    finally:
        _set_world_plugin_data(pid, world_backup, add_flag=False)

        _, inst_current = _get_plugin_and_imexporter(pid, is_loader)
        if inst_backup is not None and inst_current is not None:
            try:
                cur_bc = inst_current.GetDataInstance()
                bak_bc = inst_backup
                if cur_bc is not None and bak_bc is not None:
                    cur_bc.FlushAll()
                    bak_bc.CopyTo(cur_bc, c4d.COPYFLAGS_NONE)
            except Exception:
                pass

        try:
            c4d.SaveWorldPreferences()
        except Exception:
            pass

        c4d.EventAdd()

def build_obj_settings(scale_data):
    """Return a list of (key, value) pairs for OBJ importer settings (modern + legacy)."""
    def _resolve(*names):
        for n in names:
            v = getattr(c4d, n, None)
            if v is not None:
                return v
        return None
    k_flipz  = _resolve('OBJIMPORTOPTIONS_POINTTRANSFORM_FLIPZ', 'OBJIMPORTOPTIONS_FLIPZ')
    k_flipx  = _resolve('OBJIMPORTOPTIONS_POINTTRANSFORM_FLIPX', 'OBJIMPORTOPTIONS_FLIPX')
    k_flipy  = _resolve('OBJIMPORTOPTIONS_POINTTRANSFORM_FLIPY', 'OBJIMPORTOPTIONS_FLIPY')
    k_swapxy = _resolve('OBJIMPORTOPTIONS_POINTTRANSFORM_SWAPXY', 'OBJIMPORTOPTIONS_SWAPXY')
    k_swapxz = _resolve('OBJIMPORTOPTIONS_POINTTRANSFORM_SWAPXZ', 'OBJIMPORTOPTIONS_SWAPXZ')
    k_swapyz = _resolve('OBJIMPORTOPTIONS_POINTTRANSFORM_SWAPYZ', 'OBJIMPORTOPTIONS_SWAPYZ')

    return [
        (c4d.OBJIMPORTOPTIONS_SCALE, scale_data),
        (c4d.OBJIMPORTOPTIONS_NORMALS, c4d.OBJIMPORTOPTIONS_NORMALS_VERTEX),
        (c4d.OBJIMPORTOPTIONS_IMPORT_UVS, c4d.OBJIMPORTOPTIONS_UV_ORIGINAL),
        (c4d.OBJIMPORTOPTIONS_SPLITBY, c4d.OBJIMPORTOPTIONS_SPLITBY_OBJECT),
        (c4d.OBJIMPORTOPTIONS_MATERIAL, c4d.OBJIMPORTOPTIONS_MATERIAL_MTLFILE),
        # Axis preset: only Flip Z ON
        (k_flipz, True),
        (k_flipx, False),
        (k_flipy, False),
        (k_swapxy, False),
        (k_swapxz, False),
        (k_swapyz, False),
    ]

def build_abc_settings(scale_data):
    return [
        (c4d.ABCIMPORT_SCALE, scale_data),
    ]
