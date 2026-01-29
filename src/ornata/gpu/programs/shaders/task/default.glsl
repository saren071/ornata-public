#version 460
#extension GL_EXT_mesh_shader : require
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

// Simple task shader dispatches a fixed amount of mesh workgroups.
// For real-world culling/LOD, write meshlet counts into task payload.
layout (location=0) out uint meshGroupCount;

void main() {
    // One task workgroup requesting N mesh workgroups
    meshGroupCount = 64u; // tune per scene/meshlet count
    EmitMeshTasksEXT(meshGroupCount, 1, 1);
}
