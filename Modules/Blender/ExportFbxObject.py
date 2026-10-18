# Runs inside Blender's own Python (bpy), launched headlessly by BlenderExportScript.py via:
#   blender --background --python ExportFbxObject.py -- <blend_file> <export_dir> <unity_axis_conversion> <objects...>
import os
import sys
import bpy


class ExportFbxObject:
    def __init__(self, blend_file, export_path, object_name, unity_axis_conversion=False):
        self.blend_file = blend_file
        self.export_path = export_path
        self.object_name = object_name
        self.unity_axis_conversion = unity_axis_conversion

    def open_blend_file(self):
        bpy.ops.wm.open_mainfile(filepath=self.blend_file)
        bpy.context.view_layer.update()

    def deselect_all(self):
        if bpy.context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    def find_object(self):
        match_objects = [obj for obj in bpy.data.objects if self.object_name == obj.name]
        if not match_objects:
            print(f"ERROR: Object '{self.object_name}' not found.")
            return None

        if len(match_objects) > 1:
            print(f"WARNING: Found more than 1 object named '{self.object_name}'. Exporting the first one.")

        return match_objects[0]

    def unhide_object_and_children(self, target_object):
        target_object.hide_viewport = False
        target_object.hide_render = False
        target_object.hide_set(False)

        for child in target_object.children_recursive:
            child.hide_viewport = False
            child.hide_render = False
            child.hide_set(False)

        parent_object = target_object.parent
        while parent_object:
            parent_object.hide_viewport = False
            parent_object.hide_render = False
            parent_object.hide_set(False)
            parent_object = parent_object.parent

    def select_object_and_children(self, target_object):
        bpy.context.view_layer.objects.active = target_object
        target_object.select_set(True)
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

    def export(self):
        print("Blender version:", bpy.app.version_string)

        self.open_blend_file()
        self.deselect_all()

        target_object = self.find_object()
        if not target_object:
            return

        self.unhide_object_and_children(target_object)
        self.select_object_and_children(target_object)

        if self.unity_axis_conversion:
            print("Converting to Unity axis")
        forward_axis = '-Z' if self.unity_axis_conversion else 'Y'
        up_axis = 'Y' if self.unity_axis_conversion else 'Z'

        bpy.ops.export_scene.fbx(
            filepath=self.export_path,
            path_mode='RELATIVE',
            use_custom_props=True,
            use_selection=True,
            apply_scale_options='FBX_SCALE_UNITS',
            object_types={'EMPTY', 'MESH', 'ARMATURE'},
            axis_forward=forward_axis,
            axis_up=up_axis
        )

        print(f"Exported {target_object.name} and its children to {self.export_path}")

    @staticmethod
    def export_objects(blend_file, export_dir, unity_axis_conversion, objects_to_export):
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        for obj_name in objects_to_export:
            export_path = os.path.join(export_dir, f"{obj_name}.fbx")
            exporter = ExportFbxObject(blend_file, export_path, obj_name, unity_axis_conversion)
            exporter.export()


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: <blend_file> <export_directory> <unity_axis_conversion> <objects_to_export>")
        sys.exit(1)

    args_after_double_dash = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if args_after_double_dash:
        blend_file = args_after_double_dash[0]
        export_directory = args_after_double_dash[1]
        unity_axis_conversion = args_after_double_dash[2].lower() == 'true'
        objects_to_export = args_after_double_dash[3:]

        ExportFbxObject.export_objects(blend_file, export_directory, unity_axis_conversion, objects_to_export)
