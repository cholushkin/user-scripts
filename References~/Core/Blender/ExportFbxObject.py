import os
import bpy
import sys

class ExportFbxObject:
    def __init__(self, blend_file, export_path, object_name, unity_axis_conversion=False):
        self.blend_file = blend_file
        self.export_path = export_path
        self.object_name = object_name
        self.unity_axis_conversion = unity_axis_conversion

    def open_blend_file(self):
        bpy.ops.wm.open_mainfile(filepath=self.blend_file)
        # Ensure the scene has finished loading
        bpy.context.view_layer.update()

    def deselect_all(self):
        # Ensure we are in the right context before switching modes
        if bpy.context.object:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
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
        # Unhide the object in both the viewport and for rendering
        target_object.hide_viewport = False
        target_object.hide_render = False
        target_object.hide_set(False)  # Ensures the object is not hidden at a global level

        # Unhide its children recursively
        for child in target_object.children_recursive:  # Recursive selection of all children
            child.hide_viewport = False
            child.hide_render = False
            child.hide_set(False)

        # Unhide all parent objects recursively to ensure visibility of the entire hierarchy
        parent_object = target_object.parent
        while parent_object:
            parent_object.hide_viewport = False
            parent_object.hide_render = False
            parent_object.hide_set(False)
            parent_object = parent_object.parent

    def select_object_and_children(self, target_object):
        # Set as active object and select it
        bpy.context.view_layer.objects.active = target_object
        target_object.select_set(True)

        # Select all its children recursively
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

    def export(self):
        print("Blender version:", bpy.app.version_string)

        self.open_blend_file()
        self.deselect_all()

        target_object = self.find_object()
        if not target_object:
            return  # If object is not found, return early

        # Unhide the target object and its children before selecting them
        self.unhide_object_and_children(target_object)

        # Select the object and its children
        self.select_object_and_children(target_object)

        # Set export axis options for Unity if requested
        if self.unity_axis_conversion:
            print("Converting to Unity axis")
        forward_axis = '-Z' if self.unity_axis_conversion else 'Y'
        up_axis = 'Y' if self.unity_axis_conversion else 'Z'

        # Export the selected object(s) as FBX
        bpy.ops.export_scene.fbx(
            filepath=self.export_path,
            path_mode='RELATIVE',
            use_custom_props=True,
            use_selection=True,
            apply_scale_options='FBX_SCALE_UNITS',
            object_types={'EMPTY', 'MESH', 'ARMATURE'},
            axis_forward=forward_axis,  # Adjust forward axis for Unity
            axis_up=up_axis              # Adjust up axis for Unity
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

# Main execution for blender
if __name__ == "__main__":

    if len(sys.argv) < 5:
        print("Usage: <blend_file> <export_directory> <unity_axis_conversion> <objects_to_export>")
        sys.exit(1)

    args_after_double_dash = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if args_after_double_dash:
        blend_file = args_after_double_dash[0]  # Path to your .blend file
        export_directory = args_after_double_dash[1]  # Directory to save the FBX files
        unity_axis_conversion = args_after_double_dash[2].lower() == 'true'  # Convert the string to boolean
        objects_to_export = args_after_double_dash[3:]  # Object names to export

        # Call the export function with the parameters
        ExportFbxObject.export_objects(blend_file, export_directory, unity_axis_conversion, objects_to_export)
