import bpy
import math
from mathutils import Vector
from functools import reduce
from bpy.utils import register_classes_factory

bl_info = {
    "name": "Align by faces",
    "author": "Tom Grushka (forked from Tom Rethaller)",
    "version": (0, 2, 3),
    "blender": (2, 82, 0),
    "description": "Align two objects by their active faces",
    "warning": "",
    "category": "3D View"}


def get_ortho(a, b, c):
    if c != 0.0 and -a != b:
        return [-b-c, a, a]
    else:
        return [c, c, -a-b]


def clamp(v, min, max):
    if v < min:
        return min
    if v > max:
        return max
    return v


def align_faces(from_obj, to_obj):
    fpolys = from_obj.data.polygons
    tpolys = to_obj.data.polygons
    fpoly = fpolys[fpolys.active]
    tpoly = tpolys[tpolys.active]

    to_obj.rotation_mode = 'QUATERNION'
    tnorm = to_obj.rotation_quaternion @ tpoly.normal

    fnorm = fpoly.normal
    axis = fnorm.cross(tnorm)
    dot = fnorm.normalized().dot(tnorm.normalized())
    dot = clamp(dot, -1.0, 1.0)

    # Parallel faces need a new rotation vactor
    if axis.length < 1.0e-8:
        axis = Vector(get_ortho(fnorm.x, fnorm.y, fnorm.z))

    from_obj.rotation_mode = 'AXIS_ANGLE'
    from_obj.rotation_axis_angle = [
        math.acos(dot) + math.pi, axis[0], axis[1], axis[2]]
    bpy.context.view_layer.update()

    # Move from_obj so that faces match
    fvertices = [from_obj.data.vertices[i].co for i in fpoly.vertices]
    tvertices = [to_obj.data.vertices[i].co for i in tpoly.vertices]

    fbary = from_obj.matrix_world @ \
        (reduce(Vector.__add__, fvertices) / len(fvertices))
    tbary = to_obj.matrix_world @ \
        (reduce(Vector.__add__, tvertices) / len(tvertices))

    from_obj.location = tbary - (fbary - from_obj.location)


class OBJECT_OT_AlignByFaces(bpy.types.Operator):
    bl_label = "Align by faces"
    bl_description = "Align two objects by their active faces"
    bl_idname = "object.align_by_faces"

    @classmethod
    def poll(cls, context):
        if not len(context.selected_objects) == 2:
            return False
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                return False
        return True

    def execute(self, context):
        objs_to_move = [
            o for o in context.selected_objects if o != context.active_object]
        for o in objs_to_move:
            align_faces(o, context.active_object)
        return {'FINISHED'}


klasses = (OBJECT_OT_AlignByFaces,)
register, unregister = register_classes_factory(klasses)

if __name__ == "__main__":
    register()
