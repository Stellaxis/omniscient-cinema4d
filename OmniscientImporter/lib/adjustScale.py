import c4d
from c4d import plugins

def adjust_scale(extension, scale=1.0, unit=c4d.DOCUMENT_UNIT_M):
    plugin_id = importer_plugin_ids.get(extension)
    if plugin_id is None:
        return False

    plugin = get_plugin_by_id(plugin_id, is_loader=True)
    if plugin is None:
        return False

    scale_data = c4d.UnitScaleData()
    scale_data.SetUnitScale(scale, unit)
    
    if extension == 'abc':
        plugin[c4d.ABCIMPORT_SCALE] = scale_data
    elif extension == 'obj':
        plugin[c4d.OBJIMPORTOPTIONS_SCALE] = scale_data
        plugin[c4d.OBJIMPORTOPTIONS_NORMALS] = c4d.OBJIMPORTOPTIONS_NORMALS_VERTEX
        plugin[c4d.OBJIMPORTOPTIONS_IMPORT_UVS] = c4d.OBJIMPORTOPTIONS_UV_ORIGINAL
        plugin[c4d.OBJIMPORTOPTIONS_SPLITBY] = c4d.OBJIMPORTOPTIONS_SPLITBY_OBJECT
        plugin[c4d.OBJIMPORTOPTIONS_MATERIAL] = c4d.OBJIMPORTOPTIONS_MATERIAL_MTLFILE
    return True

importer_plugin_ids = {
    'obj': 1030177,
    'abc': 1028081,
}

def get_plugin_by_id(plugin_id, is_loader=False):
    operation = dict()
    plugin_type = c4d.PLUGINTYPE_SCENELOADER if is_loader else c4d.PLUGINTYPE_SCENESAVER
    plugin = plugins.FindPlugin(plugin_id, plugin_type)
    plugin.Message(c4d.MSG_RETRIEVEPRIVATEDATA, operation)
    return operation.get("imexporter")