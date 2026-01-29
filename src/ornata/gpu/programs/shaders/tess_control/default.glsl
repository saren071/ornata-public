#version 460 core
layout(vertices=3) out;

in VS_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } vIn[];
out TCS_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } vOut[];

layout(std140, binding=4) uniform TessUBO { float tessOuter; float tessInner; };

void main(){
    vOut[gl_InvocationID].wPos = vIn[gl_InvocationID].wPos;
    vOut[gl_InvocationID].wNrm = vIn[gl_InvocationID].wNrm;
    vOut[gl_InvocationID].uv   = vIn[gl_InvocationID].uv;
    if (gl_InvocationID==0){
        gl_TessLevelOuter[0]=tessOuter;
        gl_TessLevelOuter[1]=tessOuter;
        gl_TessLevelOuter[2]=tessOuter;
        gl_TessLevelInner[0]=tessInner;
    }
}
