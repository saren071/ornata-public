#version 460
#extension GL_EXT_mesh_shader : require

layout(local_size_x = 32, local_size_y = 1, local_size_z = 1) in;
layout(triangles, max_vertices = 128, max_primitives = 256) out;

layout(location=0) per_primitive out flat uint oPrimID[];

layout(std140, binding=0) uniform CameraUBO {
    mat4 uView; mat4 uProj; mat4 uViewProj;
    vec3 uCameraPos; float uExposure;
    vec2 uViewport;  float uTime; uint uFrameIndex;
};
layout(std430, binding=5) readonly buffer MeshPositions { vec3 pos[]; };
layout(std430, binding=6) readonly buffer MeshNormals   { vec3 nrm[]; };
layout(std430, binding=7) readonly buffer MeshUVs       { vec2 uv[];  };
layout(std430, binding=8) readonly buffer MeshIndices   { uvec3 idx[]; };

layout(location=0) out vec3 oNrm[];
layout(location=1) out vec2 oUV[];

void main(){
    uint triBase  = gl_WorkGroupID.x * 256u;
    uint triAvail = uint(idx.length());
    uint triCount = (triBase < triAvail) ? min(256u, triAvail - triBase) : 0u;

    SetMeshOutputsEXT(triCount*3u, triCount);

    for (uint t=0u; t<triCount; ++t){
        uvec3 i = idx[triBase + t];
        for (uint k=0u; k<3u; ++k){
            uint v = i[k];
            vec4 wp = vec4(pos[v],1.0);
            gl_MeshVerticesEXT[t*3u+k].gl_Position = uViewProj * wp;
            oNrm[t*3u+k] = nrm[v];
            oUV [t*3u+k] = uv[v];
        }
        gl_PrimitiveTriangleIndicesEXT[t] = uvec3(t*3u, t*3u+1u, t*3u+2u);
        oPrimID[t] = triBase + t;
    }
}
