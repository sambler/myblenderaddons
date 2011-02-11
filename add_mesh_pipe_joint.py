# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Pipe Joints",
    "author": "Buerbaum Martin (Pontiac)",
    "version": (0, 10, 7),
    "blender": (2, 5, 3),
    "api": 32411,
    "location": "View3D > Add > Mesh > Pipe Joints",
    "description": "Adds 5 pipe Joint types to the Add Mesh menu",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Add_Mesh/Add_Pipe_Joints",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=21443",
    "category": "Add Mesh"}

"""
Pipe Joints
This script lets the user create various types of pipe joints.

Usage:
You have to activated the script in the "Add-Ons" tab (user preferences).
The functionality can then be accessed via the
"Add Mesh" -> "Pipe Joints" menu.
Note: Currently only the "Elbow" type supports odd number of vertices.

Version history:
v0.10.6 - Removed "recall properties" from all functions.
    Updated various code for new API.
    API: mathutils.RotationMatrix -> mathutils.Matrix.Rotation
    API: xxx.selected -> xxx.select
    API: "invoke" function for each operator.
    Updated for new bl_info structure.
    New code for the "align_matrix".
    made script PEP8 compatible.
v0.10.5 - createFaces can now create fan/star like faces.
v0.10.4 - Updated the function "createFaces" a bit. No functional changes.
v0.10.3 - Updated store_recall_properties, apply_object_align
    and create_mesh_object.
    Changed how recall data is stored.
    Added 'description'.
v0.10.2 - API change Mathutils -> mathutils (r557)
    Fixed wiki url.
v0.10.1 - Use hidden "edit" property for "recall" operator.
v0.10 - Store "recall" properties in the created objects.
    Align the geometry to the view if the user preference says so.
v0.9.10 - Use bl_info for Add-On information.
v0.9.9 - Changed the script so it can be managed from the "Add-Ons" tab in
    the user preferences.
    Added dummy "PLUGIN" icon.
v0.9.8 - Fixed some new API stuff.
    Mainly we now have the register/unregister functions.
    Also the new() function for objects now accepts a mesh object.
    Corrected FSF address.
    Clean up of tooltips.
v0.9.7 - Use "unit" settings for angles as well.
    This also lets me use radiant for all internal values..
v0.9.6 - Use "unit" settings (i.e. none/metric/imperial).
v0.9.5 - Use mesh.from_pydata() for geometry creation.
    So we can remove unpack_list and unpack_face_list again.
v0.9.4 - Creating of the pipe now works in mesh edit mode too.
    Thanks to ideasman42 (Campbell Barton) for his nice work
    on the torus script code :-).
v0.9.3 - Changed to a saner vertex/polygon creation process (previously
    my usage of mesh.faces.add could only do quads)
    For this I've copied the functions unpack_list and unpack_face_list
    from import_scene_obj.py.
    Elbow joint actually supports 3 vertices per circle.
    Various comments.
    Script _should_ now be PEP8 compatible.
v0.9.2 - Converted from tabs to spaces (4 spaces per tab).
v0.9.1 - Converted add_mesh and add_object to their new counterparts
    "bpy.data.meshes.new() and "bpy.data.objects.new()"
v0.9 - Converted to 2.5. Made mostly pep8 compatible (exept for tabs and
    stuff the check-script didn't catch).
v0.8.5 - Fixed bug in Elbow joint. Same problem as in 0.8.1
v0.8.4 - Fixed bug in Y joint. Same problem as in 0.8.1
v0.8.3 - Fixed bug in N joint. Same problem as in 0.8.1
v0.8.2 - Fixed bug in X (cross) joint. Same problem as in 0.8.1
v0.8.1 - Fixed bug in T joint. Angles greater than 90 deg combined with a
    radius != 1 resulted in bad geometry (the radius was not taken into
    account when calculating the joint vertices).
v0.8 - Added N-Joint.
    Removed all uses of baseJointLocZ. It just clutters the code.
v0.7 - Added cross joint
v0.6 - No visible changes. Lots of internal ones though
    (complete redesign of face creation process).
    As a bonus the code is a bit easier to read now.
    Added a nice&simple little "bridge" function
    (createFaces) for these changes.
v0.5.1 - Made it possible to create asymmetric Y joints.
    Renamed the 2 Wye Joints to something more fitting and unique.
    One is now the Tee joint, the second one remains the Wye joint.
v0.5 - Added real Y joint.
v0.4.3 - Added check for odd vertex numbers. They are not (yet) supported.
v0.4.2 - Added pipe length to the GUI.
v0.4.1 - Removed the unfinished menu entries for now.
v0.4 - Tried to clean up the face creation in addTeeJoint
v0.3 - Code for wye (Y) shape (straight pipe with "branch" for now)
v0.2 - Restructured to allow different types of pipe (joints).
v0.1 - Initial revision.

More links:
http://gitorious.org/blender-scripts/blender-pipe-joint-script
http://blenderartists.org/forum/showthread.php?t=154394

TODO:

Use a rotation matrix for rotating the circle vertices:
rotation_matrix = mathutils.Matrix.Rotation(-math.pi/2, 4, 'x')
mesh.transform(rotation_matrix)
"""

import bpy
import mathutils
from math import *
from bpy.props import *


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
def create_mesh_object(context, verts, edges, faces, name):
    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    import add_object_utils
    return add_object_utils.object_data_add(context, mesh, operator=None)

# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create
#       a fan/star of faces.
# Note: If both vertex idx list are the same length they have
#       to have at least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces


class AddElbowJoint(bpy.types.Operator):
    # Create the vertices and polygons for a simple elbow (bent pipe).
    '''Add an Elbow pipe mesh'''
    bl_idname = "mesh.primitive_elbow_joint_add"
    bl_label = "Add Pipe Elbow"
    bl_options = {'REGISTER', 'UNDO'}

    radius = FloatProperty(name="Radius",
        description="The radius of the pipe.",
        default=1.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    div = IntProperty(name="Divisions",
        description="Number of vertices (divisions).",
        default=32, min=3, max=256)

    angle = FloatProperty(name="Angle",
        description="The angle of the branching pipe (i.e. the 'arm')." \
            " Measured from the center line of the main pipe.",
        default=radians(45.0),
        min=radians(-179.9),
        max=radians(179.9),
        unit="ROTATION")

    startLength = FloatProperty(name="Length Start",
        description="Length of the beginning of the pipe.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    endLength = FloatProperty(name="End Length",
        description="Length of the end of the pipe.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")

    def execute(self, context):

        radius = self.radius
        div = self.div

        angle = self.angle

        startLength = self.startLength
        endLength = self.endLength

        verts = []
        faces = []

        loop1 = []        # The starting circle
        loop2 = []        # The elbow circle
        loop3 = []        # The end circle

        # Create start circle
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)
            locZ = -startLength
            loop1.append(len(verts))
            verts.append([locX * radius, locY * radius, locZ])

        # Create deformed joint circle
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)
            locZ = locX * tan(angle / 2.0)
            loop2.append(len(verts))
            verts.append([locX * radius, locY * radius, locZ * radius])

        # Create end circle
        baseEndLocX = -endLength * sin(angle)
        baseEndLocZ = endLength * cos(angle)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 - angle)
            locX = locX * sin(pi / 2.0 - angle)

            loop3.append(len(verts))
            # Translate and add circle vertices to the list.
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create faces
        faces.extend(createFaces(loop1, loop2, closed=True))
        faces.extend(createFaces(loop2, loop3, closed=True))

        base = create_mesh_object(context, verts, [], faces, "Elbow Joint")

        return {'FINISHED'}


class AddTeeJoint(bpy.types.Operator):
    # Create the vertices and polygons for a simple tee (T) joint.
    # The base arm of the T can be positioned in an angle if needed though.
    '''Add a Tee-Joint mesh'''
    bl_idname = "mesh.primitive_tee_joint_add"
    bl_label = "Add Pipe Tee-Joint"
    bl_options = {'REGISTER', 'UNDO'}

    radius = FloatProperty(name="Radius",
        description="The radius of the pipe.",
        default=1.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    div = IntProperty(name="Divisions",
        description="Number of vertices (divisions).",
        default=32,
        min=4,
        max=256)

    angle = FloatProperty(name="Angle",
        description="The angle of the branching pipe (i.e. the 'arm')." \
            " Measured from the center line of the main pipe.",
        default=radians(90.0),
        min=radians(0.1),
        max=radians(179.9),
        unit="ROTATION")

    startLength = FloatProperty(name="Length Start",
        description="Length of the beginning of the" \
            " main pipe (the straight one).",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    endLength = FloatProperty(name="End Length",
        description="Length of the end of the" \
            " main pipe (the straight one).",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    branchLength = FloatProperty(name="Arm Length",
        description="Length of the arm pipe (the bent one).",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")

    def execute(self, context):

        radius = self.radius
        div = self.div

        angle = self.angle

        startLength = self.startLength
        endLength = self.endLength
        branchLength = self.branchLength

        if (div % 2):
            # Odd vertice number not supported (yet).
            return {'CANCELLED'}

        verts = []
        faces = []

        # List of vert indices of each cross section
        loopMainStart = []        # Vert indices for the
                                  # beginning of the main pipe.
        loopJoint1 = []        # Vert indices for joint that is used
                               # to connect the joint & loopMainStart.
        loopJoint2 = []        # Vert indices for joint that is used
                               # to connect the joint & loopArm.
        loopJoint3 = []        # Vert index for joint that is used
                               # to connect the joint & loopMainEnd.
        loopArm = []        # Vert indices for the end of the arm.
        loopMainEnd = []        # Vert indices for the
                                # end of the main pipe.

        # Create start circle (main pipe)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)
            locZ = -startLength
            loopMainStart.append(len(verts))
            verts.append([locX * radius, locY * radius, locZ])

        # Create deformed joint circle
        vertTemp1 = None
        vertTemp2 = None
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)

            if vertIdx == 0:
                vertTemp1 = len(verts)
            if vertIdx == div / 2:
                # @todo: This will possibly break if we
                # ever support odd divisions.
                vertTemp2 = len(verts)

            loopJoint1.append(len(verts))
            if (vertIdx < div / 2):
                # Straight side of main pipe.
                locZ = 0
                loopJoint3.append(len(verts))
            else:
                # Branching side
                locZ = locX * tan(angle / 2.0)
                loopJoint2.append(len(verts))

            verts.append([locX * radius, locY * radius, locZ * radius])

        # Create 2. deformed joint (half-)circle
        loopTemp = []
        for vertIdx in range(div):
            if (vertIdx > div / 2):
                curVertAngle = vertIdx * (2.0 * pi / div)
                locX = sin(curVertAngle)
                locY = -cos(curVertAngle)
                locZ = -(radius * locX * tan((pi - angle) / 2.0))
                loopTemp.append(len(verts))
                verts.append([locX * radius, locY * radius, locZ])

        loopTemp2 = loopTemp[:]

        # Finalise 2. loop
        loopTemp.reverse()
        loopTemp.append(vertTemp1)
        loopJoint2.reverse()
        loopJoint2.extend(loopTemp)
        loopJoint2.reverse()

        # Finalise 3. loop
        loopTemp2.append(vertTemp2)
        loopTemp2.reverse()
        loopJoint3.extend(loopTemp2)

        # Create end circle (branching pipe)
        baseEndLocX = -branchLength * sin(angle)
        baseEndLocZ = branchLength * cos(angle)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 - angle)
            locX = locX * sin(pi / 2.0 - angle)

            loopArm.append(len(verts))

            # Add translated circle.
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create end circle (main pipe)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)
            locZ = endLength
            loopMainEnd.append(len(verts))
            verts.append([locX * radius, locY * radius, locZ])

        # Create faces
        faces.extend(createFaces(loopMainStart, loopJoint1, closed=True))
        faces.extend(createFaces(loopJoint2, loopArm, closed=True))
        faces.extend(createFaces(loopJoint3, loopMainEnd, closed=True))

        base = create_mesh_object(context, verts, [], faces, "Tee Joint")

        return {'FINISHED'}


class AddWyeJoint(bpy.types.Operator):
    '''Add a Wye-Joint mesh'''
    bl_idname = "mesh.primitive_wye_joint_add"
    bl_label = "Add Pipe Wye-Joint"
    bl_options = {'REGISTER', 'UNDO'}

    radius = FloatProperty(name="Radius",
        description="The radius of the pipe.",
        default=1.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    div = IntProperty(name="Divisions",
        description="Number of vertices (divisions).",
        default=32,
        min=4,
        max=256)

    angle1 = FloatProperty(name="Angle 1",
        description="The angle of the 1. branching pipe." \
            " Measured from the center line of the main pipe.",
        default=radians(45.0),
        min=radians(-179.9),
        max=radians(179.9),
        unit="ROTATION")
    angle2 = FloatProperty(name="Angle 2",
        description="The angle of the 2. branching pipe." \
            " Measured from the center line of the main pipe.",
        default=radians(45.0),
        min=radians(-179.9),
        max=radians(179.9),
        unit="ROTATION")

    startLength = FloatProperty(name="Length Start",
        description="Length of the beginning of the" \
            " main pipe (the straight one).",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    branch1Length = FloatProperty(name="Length Arm 1",
        description="Length of the 1. arm.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    branch2Length = FloatProperty(name="Length Arm 2",
        description="Length of the 2. arm.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")

    def execute(self, context):

        radius = self.radius
        div = self.div

        angle1 = self.angle1
        angle2 = self.angle2

        startLength = self.startLength
        branch1Length = self.branch1Length
        branch2Length = self.branch2Length

        if (div % 2):
            # Odd vertice number not supported (yet).
            return {'CANCELLED'}

        verts = []
        faces = []

        # List of vert indices of each cross section
        loopMainStart = []        # Vert indices for
                                  # the beginning of the main pipe.
        loopJoint1 = []        # Vert index for joint that is used
                               # to connect the joint & loopMainStart.
        loopJoint2 = []        # Vert index for joint that
                               # is used to connect the joint & loopArm1.
        loopJoint3 = []        # Vert index for joint that is
                               # used to connect the joint & loopArm2.
        loopArm1 = []        # Vert idxs for end of the 1. arm.
        loopArm2 = []        # Vert idxs for end of the 2. arm.

        # Create start circle
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)
            locZ = -startLength
            loopMainStart.append(len(verts))
            verts.append([locX * radius, locY * radius, locZ])

        # Create deformed joint circle
        vertTemp1 = None
        vertTemp2 = None
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)

            if vertIdx == 0:
                vertTemp2 = len(verts)
            if vertIdx == div / 2:
                # @todo: This will possibly break if we
                # ever support odd divisions.
                vertTemp1 = len(verts)

            loopJoint1.append(len(verts))
            if (vertIdx > div / 2):
                locZ = locX * tan(angle1 / 2.0)
                loopJoint2.append(len(verts))
            else:
                locZ = locX * tan(-angle2 / 2.0)
                loopJoint3.append(len(verts))

            verts.append([locX * radius, locY * radius, locZ * radius])

        # Create 2. deformed joint (half-)circle
        loopTemp = []
        angleJoint = (angle2 - angle1) / 2.0
        for vertIdx in range(div):
            if (vertIdx > div / 2):
                curVertAngle = vertIdx * (2.0 * pi / div)

                locX = (-sin(curVertAngle) * sin(angleJoint)
                    / sin(angle2 - angleJoint))
                locY = -cos(curVertAngle)
                locZ = (-(sin(curVertAngle) * cos(angleJoint)
                    / sin(angle2 - angleJoint)))

                loopTemp.append(len(verts))
                verts.append([locX * radius, locY * radius, locZ * radius])

        loopTemp2 = loopTemp[:]

        # Finalise 2. loop
        loopTemp.append(vertTemp1)
        loopTemp.reverse()
        loopTemp.append(vertTemp2)
        loopJoint2.reverse()
        loopJoint2.extend(loopTemp)
        loopJoint2.reverse()

        # Finalise 3. loop
        loopTemp2.reverse()
        loopJoint3.extend(loopTemp2)

        # Create end circle (1. branching pipe)
        baseEndLocX = -branch1Length * sin(angle1)
        baseEndLocZ = branch1Length * cos(angle1)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 - angle1)
            locX = locX * sin(pi / 2.0 - angle1)

            loopArm1.append(len(verts))
            # Add translated circle.
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create end circle (2. branching pipe)
        baseEndLocX = branch2Length * sin(angle2)
        baseEndLocZ = branch2Length * cos(angle2)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 + angle2)
            locX = locX * sin(pi / 2.0 + angle2)

            loopArm2.append(len(verts))
            # Add translated circle
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create faces
        faces.extend(createFaces(loopMainStart, loopJoint1, closed=True))
        faces.extend(createFaces(loopJoint2, loopArm1, closed=True))
        faces.extend(createFaces(loopJoint3, loopArm2, closed=True))

        base = create_mesh_object(context, verts, [], faces, "Wye Joint")

        return {'FINISHED'}


class AddCrossJoint(bpy.types.Operator):
    '''Add a Cross-Joint mesh'''
    # Create the vertices and polygons for a coss (+ or X) pipe joint.
    bl_idname = "mesh.primitive_cross_joint_add"
    bl_label = "Add Pipe Cross-Joint"
    bl_options = {'REGISTER', 'UNDO'}

    radius = FloatProperty(name="Radius",
        description="The radius of the pipe.",
        default=1.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    div = IntProperty(name="Divisions",
        description="Number of vertices (divisions).",
        default=32,
        min=4,
        max=256)

    angle1 = FloatProperty(name="Angle 1",
        description="The angle of the 1. arm (from the main axis).",
        default=radians(90.0),
        min=radians(-179.9),
        max=radians(179.9),
        unit="ROTATION")
    angle2 = FloatProperty(name="Angle 2",
        description="The angle of the 2. arm (from the main axis).",
        default=radians(90.0),
        min=radians(-179.9),
        max=radians(179.9),
        unit="ROTATION")
    angle3 = FloatProperty(name="Angle 3 (center)",
        description="The angle of the center arm (from the main axis).",
        default=radians(0.0),
        min=radians(-179.9),
        max=radians(179.9),
        unit="ROTATION")

    startLength = FloatProperty(name="Length Start",
        description="Length of the beginning of the " \
                "main pipe (the straight one).",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    branch1Length = FloatProperty(name="Length Arm 1",
        description="Length of the 1. arm.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    branch2Length = FloatProperty(name="Length Arm 2",
        description="Length of the 2. arm.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    branch3Length = FloatProperty(name="Length Arm 3 (center)",
        description="Length of the center arm.",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")

    def execute(self, context):

        radius = self.radius
        div = self.div

        angle1 = self.angle1
        angle2 = self.angle2
        angle3 = self.angle3

        startLength = self.startLength
        branch1Length = self.branch1Length
        branch2Length = self.branch2Length
        branch3Length = self.branch3Length
        if (div % 2):
            # Odd vertice number not supported (yet).
            return {'CANCELLED'}

        verts = []
        faces = []

        # List of vert indices of each cross section
        loopMainStart = []        # Vert indices for the
                                  # beginning of the main pipe.
        loopJoint1 = []        # Vert index for joint that is used
                               # to connect the joint & loopMainStart.
        loopJoint2 = []        # Vert index for joint that is used
                               # to connect the joint & loopArm1.
        loopJoint3 = []        # Vert index for joint that is used
                               # to connect the joint & loopArm2.
        loopJoint4 = []        # Vert index for joint that is used
                               # to connect the joint & loopArm3.
        loopArm1 = []        # Vert idxs for the end of the 1. arm.
        loopArm2 = []        # Vert idxs for the end of the 2. arm.
        loopArm3 = []        # Vert idxs for the center arm end.

        # Create start circle
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)
            locZ = -startLength
            loopMainStart.append(len(verts))
            verts.append([locX * radius, locY * radius, locZ])

        # Create 1. deformed joint circle
        vertTemp1 = None
        vertTemp2 = None
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            locX = sin(curVertAngle)
            locY = cos(curVertAngle)

            if vertIdx == 0:
                vertTemp2 = len(verts)
            if vertIdx == div / 2:
                # @todo: This will possibly break if we
                # ever support odd divisions.
                vertTemp1 = len(verts)

            loopJoint1.append(len(verts))
            if (vertIdx > div / 2):
                locZ = locX * tan(angle1 / 2.0)
                loopJoint2.append(len(verts))
            else:
                locZ = locX * tan(-angle2 / 2.0)
                loopJoint3.append(len(verts))

            verts.append([locX * radius, locY * radius, locZ * radius])

        loopTemp2 = loopJoint2[:]

        # Create 2. deformed joint circle
        loopTempA = []
        loopTempB = []
        angleJoint1 = (angle1 - angle3) / 2.0
        angleJoint2 = (angle2 + angle3) / 2.0
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)

            # Skip pole vertices
            # @todo: This will possibly break if
            # we ever support odd divisions.
            if not (vertIdx == 0) and not (vertIdx == div / 2):

                if (vertIdx > div / 2):
                    angleJoint = angleJoint1
                    angle = angle1
                    Z = -1.0
                    loopTempA.append(len(verts))

                else:
                    angleJoint = angleJoint2
                    angle = angle2
                    Z = 1.0
                    loopTempB.append(len(verts))

                locX = (sin(curVertAngle) * sin(angleJoint)
                    / sin(angle - angleJoint))
                locY = -cos(curVertAngle)
                locZ = (Z * (sin(curVertAngle) * cos(angleJoint)
                    / sin(angle - angleJoint)))

                verts.append([locX * radius, locY * radius, locZ * radius])

        loopTempA2 = loopTempA[:]
        loopTempB2 = loopTempB[:]
        loopTempB3 = loopTempB[:]

        # Finalise 2. loop
        loopTempA.append(vertTemp1)
        loopTempA.reverse()
        loopTempA.append(vertTemp2)
        loopJoint2.reverse()
        loopJoint2.extend(loopTempA)
        loopJoint2.reverse()

        # Finalise 3. loop
        loopJoint3.extend(loopTempB3)

        # Finalise 4. loop
        loopTempA2.append(vertTemp1)
        loopTempA2.reverse()
        loopTempB2.append(vertTemp2)
        loopJoint4.extend(reversed(loopTempB2))
        loopJoint4.extend(loopTempA2)

        # Create end circle (1. branching pipe)
        baseEndLocX = -branch1Length * sin(angle1)
        baseEndLocZ = branch1Length * cos(angle1)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 - angle1)
            locX = locX * sin(pi / 2.0 - angle1)

            loopArm1.append(len(verts))
            # Add translated circle.
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create end circle (2. branching pipe)
        baseEndLocX = branch2Length * sin(angle2)
        baseEndLocZ = branch2Length * cos(angle2)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 + angle2)
            locX = locX * sin(pi / 2.0 + angle2)

            loopArm2.append(len(verts))
            # Add translated circle
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create end circle (center pipe)
        baseEndLocX = branch3Length * sin(angle3)
        baseEndLocZ = branch3Length * cos(angle3)
        for vertIdx in range(div):
            curVertAngle = vertIdx * (2.0 * pi / div)
            # Create circle
            locX = sin(curVertAngle) * radius
            locY = cos(curVertAngle) * radius
            locZ = 0.0

            # Rotate circle
            locZ = locX * cos(pi / 2.0 + angle3)
            locX = locX * sin(pi / 2.0 + angle3)

            loopArm3.append(len(verts))
            # Add translated circle
            verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

        # Create faces
        faces.extend(createFaces(loopMainStart, loopJoint1, closed=True))
        faces.extend(createFaces(loopJoint2, loopArm1, closed=True))
        faces.extend(createFaces(loopJoint3, loopArm2, closed=True))
        faces.extend(createFaces(loopJoint4, loopArm3, closed=True))

        base = create_mesh_object(context, verts, [], faces, "Cross Joint")

        return {'FINISHED'}


class AddNJoint(bpy.types.Operator):
    '''Add a N-Joint mesh'''
    # Create the vertices and polygons for a regular n-joint.
    bl_idname = "mesh.primitive_n_joint_add"
    bl_label = "Add Pipe N-Joint"
    bl_options = {'REGISTER', 'UNDO'}

    radius = FloatProperty(name="Radius",
        description="The radius of the pipe.",
        default=1.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    div = IntProperty(name="Divisions",
        description="Number of vertices (divisions).",
        default=32,
        min=4,
        max=256)
    number = IntProperty(name="Arms/Joints",
        description="Number of joints/arms",
        default=5,
        min=2,
        max=99999)
    length = FloatProperty(name="Length",
        description="Length of each joint/arm",
        default=3.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")

    def execute(self, context):
        radius = self.radius
        div = self.div
        number = self.number
        length = self.length

        if (div % 2):
            # Odd vertice number not supported (yet).
            return {'CANCELLED'}

        if (number < 2):
            return {'CANCELLED'}

        verts = []
        faces = []

        loopsEndCircles = []
        loopsJointsTemp = []
        loopsJoints = []

        vertTemp1 = None
        vertTemp2 = None

        angleDiv = (2.0 * pi / number)

        # Create vertices for the end circles.
        for num in range(number):
            circle = []
            # Create start circle
            angle = num * angleDiv

            baseEndLocX = length * sin(angle)
            baseEndLocZ = length * cos(angle)
            for vertIdx in range(div):
                curVertAngle = vertIdx * (2.0 * pi / div)
                # Create circle
                locX = sin(curVertAngle) * radius
                locY = cos(curVertAngle) * radius
                locZ = 0.0

                # Rotate circle
                locZ = locX * cos(pi / 2.0 + angle)
                locX = locX * sin(pi / 2.0 + angle)

                circle.append(len(verts))
                # Add translated circle
                verts.append([baseEndLocX + locX, locY, baseEndLocZ + locZ])

            loopsEndCircles.append(circle)

            # Create vertices for the joint circles.
            loopJoint = []
            for vertIdx in range(div):
                curVertAngle = vertIdx * (2.0 * pi / div)
                locX = sin(curVertAngle)
                locY = cos(curVertAngle)

                skipVert = False
                # Store pole vertices
                if vertIdx == 0:
                    if (num == 0):
                        vertTemp2 = len(verts)
                    else:
                        skipVert = True
                elif vertIdx == div / 2:
                    # @todo: This will possibly break if we
                    # ever support odd divisions.
                    if (num == 0):
                        vertTemp1 = len(verts)
                    else:
                        skipVert = True

                if not skipVert:
                    if (vertIdx > div / 2):
                        locZ = -locX * tan((pi - angleDiv) / 2.0)
                        loopJoint.append(len(verts))

                        # Rotate the vert
                        cosAng = cos(-angle)
                        sinAng = sin(-angle)
                        LocXnew = locX * cosAng - locZ * sinAng
                        LocZnew = locZ * cosAng + locX * sinAng
                        locZ = LocZnew
                        locX = LocXnew

                        verts.append([
                            locX * radius,
                            locY * radius,
                            locZ * radius])
                    else:
                        # These two vertices will only be
                        # added the very first time.
                        if vertIdx == 0 or vertIdx == div / 2:
                            verts.append([locX * radius, locY * radius, locZ])

            loopsJointsTemp.append(loopJoint)

        # Create complete loops (loopsJoints) out of the
        # double number of half loops in loopsJointsTemp.
        for halfLoopIdx in range(len(loopsJointsTemp)):
            if (halfLoopIdx == len(loopsJointsTemp) - 1):
                idx1 = halfLoopIdx
                idx2 = 0
            else:
                idx1 = halfLoopIdx
                idx2 = halfLoopIdx + 1

            loopJoint = []
            loopJoint.append(vertTemp2)
            loopJoint.extend(reversed(loopsJointsTemp[idx2]))
            loopJoint.append(vertTemp1)
            loopJoint.extend(loopsJointsTemp[idx1])

            loopsJoints.append(loopJoint)

        # Create faces from the two
        # loop arrays (loopsJoints -> loopsEndCircles).
        for loopIdx in range(len(loopsEndCircles)):
            faces.extend(
                createFaces(loopsJoints[loopIdx],
                loopsEndCircles[loopIdx], closed=True))

        base = create_mesh_object(context, verts, [], faces, "N Joint")

        return {'FINISHED'}


class INFO_MT_mesh_pipe_joints_add(bpy.types.Menu):
    # Define the "Pipe Joints" menu
    bl_idname = "INFO_MT_mesh_pipe_joints_add"
    bl_label = "Pipe Joints"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_elbow_joint_add",
            text="Pipe Elbow")
        layout.operator("mesh.primitive_tee_joint_add",
            text="Pipe T-Joint")
        layout.operator("mesh.primitive_wye_joint_add",
            text="Pipe Y-Joint")
        layout.operator("mesh.primitive_cross_joint_add",
            text="Pipe Cross-Joint")
        layout.operator("mesh.primitive_n_joint_add",
            text="Pipe N-Joint")

################################

import space_info


# Define "Pipe Joints" menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_mesh_pipe_joints_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Pipe Joints" menu to the "Add Mesh" menu
    space_info.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Pipe Joints" menu from the "Add Mesh" menu.
    space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
