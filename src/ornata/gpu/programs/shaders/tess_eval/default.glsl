#version 460 core
layout(triangles, equal_spacing, ccw) in;

in TCS_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } tIn[];
out TES_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } tOut;

layout(std140, binding=0) uniform CameraUBO {
    mat4 uView; mat4 uProj; mat4 uViewProj;
    vec3 uCameraPos; float uExposure;
    vec2 uViewport;  float uTime; uint uFrameIndex;
};

void main(){
    vec3 b = vec3(gl_TessCoord.x, gl_TessCoord.y, gl_TessCoord.z);
    tOut.wPos = tIn[0].wPos*b.x + tIn[1].wPos*b.y + tIn[2].wPos*b.z;
    tOut.wNrm = normalize(tIn[0].wNrm*b.x + tIn[1].wNrm*b.y + tIn[2].wNrm*b.z);
    tOut.uv   = tIn[0].uv*b.x   + tIn[1].uv*b.y   + tIn[2].uv*b.z;
    gl_Position = uViewProj * vec4(tOut.wPos,1.0);
}
